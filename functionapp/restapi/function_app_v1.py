import json  # to handle output as json
import logging
import os
import time
import uuid

import azure.functions as func
import requests


def install(package):
    from importlib import import_module

    try:
        import_module(package)
    except ImportError:
        import subprocess

        subprocess.check_call(["python", "-m", "pip", "-q", "install", package])


for package in ["langchain", "langchain-openai", "pdfminer.six", "azurefunctions-extensions-bindings-blob"]:
    install(package)

import azurefunctions.extensions.bindings.blob as blob
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from pdfminer.high_level import extract_text

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def generate_id(batchids: []):
    batchid = str(uuid.uuid4())
    if batchid in batchids:
        return generate_id()
    return batchid


def upload_blob_data(self, blob_service_client: blob.BlobClient, container_name: str, blob_name: str, data: bytes):
    blob_client = blob_service_client.get_blob_client(container=container_name, blob="sample-blob.txt")
    # Upload the blob data - default blob type is BlockBlob
    blob_client.upload_blob(data, blob_type="BlockBlob")


@app.route(route="batch/generate_id", methods=["GET"])
@app.cosmos_db_input(
    arg_name="books",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="files",
    sql_query="SELECT * FROM c",
)
def generate_batchid(
    req: func.HttpRequest, books: func.DocumentList
) -> func.HttpResponse:
    books_serializable = [dict(book) for book in books]

    batchids = [
        book["batchid"] if "batchid" in book else "" for book in books_serializable
    ]

    new_batchid = generate_id(batchids)

    return func.HttpResponse(json.dumps({"batchid": new_batchid}), status_code=200)


@app.route(route="batch/{batchid}/create", methods=["POST"])
@app.cosmos_db_output(
    arg_name="outputDB",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="files",
)
@app.cosmos_db_input(
    arg_name="files",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="files",
    sql_query="SELECT * FROM c",
)
# @app.blob_output(
#     arg_name="outputBlob",
#     connection="AzureWebJobsStorage",
#     path="output/{batchid}/{fileid}/{filename}",
#     create_if_not_exists=True,
# )
def create_batch(
    req: func.HttpRequest,
    outputDB: func.Out[func.Document],
    # outputBlob: func.Out[str],
    files: func.DocumentList
) -> func.HttpResponse:
    files = req.files.getlist("files")
    if len(files) == 0:
        return func.HttpResponse(
            json.dumps({"message": "No files provided"}), status_code=400
        )

    file_to_upload = files[0]
    batchid = req.route_params["batchid"]

    for fileid in range(len(files)):
        file_to_upload = files[fileid]
        logging.info(file_to_upload)
        filename = file_to_upload.filename
        logging.info(f"Uploading file {filename} to batch {batchid}")
        blob_service_client = BlobServiceClient.from_connection_string(
            os.getenv("AzureWebJobsStorage")
        )
        container_name = "output/{batchid}/{fileid}"
        upload_blob_data(blob_service_client, container_name, filename, file_to_upload.stream.read())

        logging.info(f"File {filename} uploaded to batch {batchid}")
        # save metadata to cosmos db
        outputDB.set(
            func.Document.from_dict(
                {
                    "id": str(len(files) + 1),
                    "batchid": batchid,
                    "filename": filename,
                    "size": file_to_upload.content_length,
                    "content_type": file_to_upload.content_type,
                    "filepath": f"output/{batchid}/{fileid}/{filename}",
                }
            )
        )

    return func.HttpResponse(json.dumps({"message": "Batch created"}), status_code=200)


@app.route(route="batch/{batchid}/books", methods=["GET"])
@app.cosmos_db_input(
    arg_name="books",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="files",
    sql_query="SELECT * FROM c where c.batchid = {batchid}",
)
def get_books(req: func.HttpRequest, books: func.DocumentList) -> func.HttpResponse:
    books_serializable = [dict(book) for book in books]
    return func.HttpResponse(json.dumps({"books": books_serializable}), status_code=200)


@app.route(route="batch/{batchid}/process", methods=["GET"])
@app.cosmos_db_input(
    arg_name="batches",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="batch",
    sql_query="SELECT * FROM c",
    # partition_key="{batchid}"
)
@app.cosmos_db_input(
    arg_name="files",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="files",
    sql_query="SELECT * FROM c where c.batchid = {batchid}",
    # partition_key="{batchid}"
)
@app.cosmos_db_output(
    arg_name="outputDB",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="batch",
    # partition_key="{batchid}"
)
@app.queue_output(
    arg_name="textExtractionQueue",
    queue_name="text-extraction-queue",
    connection="AzureWebJobsStorage",
)
def process_batch(
    req: func.HttpRequest,
    batches: func.DocumentList,
    files: func.DocumentList,
    outputDB: func.Out[func.Document],
    textExtractionQueue: func.Out[str],
) -> func.HttpResponse:
    batchid = req.route_params["batchid"]
    logging.info(f"Starting batch {batchid}")
    logging.info(batches)
    batches_list = [dict(batch) for batch in batches]
    batchids_list = [batch["batchid"] for batch in batches_list]

    if batchid not in batchids_list:
        new_batch_to_process = {
            "id": str(len(batches_list) + 1),
            "batchid": batchid,
            "text_extraction_status": "pending",
            "text_extraction_message": "",
            "text_extraction_start_time": "",
            "text_extraction_end_time": "",
            "sow_extraction_status": "pending",
            "sow_extraction_message": "",
            "sow_extraction_start_time": "",
            "sow_extraction_end_time": "",
        }
        outputDB.set(func.Document.from_dict(new_batch_to_process))
        textExtractionQueue.set(json.dumps({"batch": new_batch_to_process, "files": files}))
        return func.HttpResponse(
            json.dumps(
                {
                    "message": "Started the processing of the batch",
                    "data": new_batch_to_process,
                }
            ),
            status_code=201,
        )
    else:
        matched_batch = [batch for batch in batches_list if batch["batchid"] == batchid][0]
        return func.HttpResponse(
            json.dumps(
                {
                    "message": "Batch is being processed, please wait",
                    "data": matched_batch,
                }
            ), status_code=200
        )


@app.queue_trigger(
    arg_name="textExtractionQueue",
    queue_name="text-extraction-queue",
    connection="AzureWebJobsStorage",
)
@app.queue_output(
    arg_name="startSOWExtractionQueue",
    queue_name="sow-extraction-queue",
    connection="AzureWebJobsStorage",
)
@app.cosmos_db_output(
    arg_name="outputDB",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="batch",
    # partition_key="{batchid}"
)
@app.cosmos_db_output(
    arg_name="filesOutputDB",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="files",
    # partition_key="{batchid}"
)
def text_extraction(
    textExtractionQueue: func.QueueMessage,
    startSOWExtractionQueue: func.Out[str],
    outputDB: func.Out[func.Document],
    filesOutputDB: func.Out[func.Document],
) -> None:
    logging.info("Text extraction started")
    parse_json = json.loads(textExtractionQueue.get_body().decode("utf-8"))
    batch = parse_json["batch"]
    files = parse_json["files"]
    text_extraction_start_time = time.time()
    batch["text_extraction_status"] = "processing"
    outputDB.set(func.Document.from_dict(batch))
    logging.info("Text extraction in progress...")

    for file in files:
        if file["batchid"] == batch["batchid"]:
            # Extract text
            reader = extract_text(file["filepath"])
            text = reader.pages[0]
            file["extracted_text"] = text
            filesOutputDB.set(func.Document.from_dict(file))

    batch["text_extraction_status"] = "completed"
    text_extraction_end_time = time.time()
    batch["text_extraction_start_time"] = str(text_extraction_start_time)
    batch["text_extraction_end_time"] = str(text_extraction_end_time)
    outputDB.set(func.Document.from_dict(batch))
    startSOWExtractionQueue.set(json.dumps({"batch": batch, "files": files}))
    logging.info("Text extraction completed")


@app.queue_trigger(
    arg_name="startSOWExtractionQueue",
    queue_name="sow-extraction-queue",
    connection="AzureWebJobsStorage",
)
@app.cosmos_db_output(
    arg_name="outputDB",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="batch",
    # partition_key="{batchid}"
)
@app.cosmos_db_input(
    arg_name="books",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="files",
    sql_query="SELECT * FROM c",
    # partition_key="{batchid}"
)
@app.cosmos_db_output(
    arg_name="bookOutputDB",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="files",
    # partition_key="{batchid}"
)
def sow_extraction(
    startSOWExtractionQueue: func.QueueMessage, outputDB: func.Out[func.Document],
    books: func.DocumentList, bookOutputDB: func.Out[func.Document]
) -> None:
    batch = json.loads(startSOWExtractionQueue.get_body().decode("utf-8"))
    sow_extraction_start_time = time.time()
    batch["sow_extraction_status"] = "processing"
    for book in books:
        if book["batchid"] == batch["batchid"]:
            # Extract SOW
            text = book["extracted_text"]
            time.sleep(5)
            book["sow"] = "Statement of Work"
            bookOutputDB.set(func.Document.from_dict(book))

    batch["sow_extraction_status"] = "completed"
    sow_extraction_end_time = time.time()
    batch["sow_extraction_start_time"] = str(sow_extraction_start_time)
    batch["sow_extraction_end_time"] = str(sow_extraction_end_time)
    outputDB.set(func.Document.from_dict(batch))



@app.route(route="test/extract", methods=["GET"])
def extract_text(req: func.HttpRequest) -> func.HttpResponse:
    reader = PdfReader("killm.pdf")
    page = reader.pages[0]
    text = page.extract_text()
    return func.HttpResponse(json.dumps({"text": text}), status_code=200)


@app.route(route="test/openai", methods=["GET"])
def openai_response(req: func.HttpRequest) -> func.HttpResponse:
    response = requests.post(
        "https://llmfoundry.straive.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImphaXByYWthc2guc2l5eWFkcmlAZ3JhbWVuZXIuY29tIn0.9o34ZqnU3it_tf1uGSO04xHo3YYoDRNCCkPj1NciLx0:my-test-project"
        },
        json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "What is 2 + 2"}],
        },
    )
    # print(response.json())
    return func.HttpResponse(json.dumps({"message": response.json()}), status_code=200)


@app.route(route="test/langchain", methods=["GET"])
def langchain_response(req: func.HttpRequest) -> func.HttpResponse:
    chat_model = ChatOpenAI(
        openai_api_base="https://llmfoundry.straive.com/openai/v1/",
        openai_api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImphaXByYWthc2guc2l5eWFkcmlAZ3JhbWVuZXIuY29tIn0.9o34ZqnU3it_tf1uGSO04xHo3YYoDRNCCkPj1NciLx0:my-test-project",
    )
    messages = [HumanMessage(content="What is 2 + 2?")]
    print(chat_model.invoke(messages).json())
    return func.HttpResponse(
        json.dumps({"message": chat_model.invoke(messages).json()}), status_code=200
    )
