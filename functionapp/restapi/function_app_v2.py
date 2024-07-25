import base64
import io
import json  # to handle output as json
import logging
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


for package in ["langchain", "langchain-openai", "pdfminer.six"]:
    install(package)

import gzip

from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from pdfminer.converter import TextConverter
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pypdf import PdfReader

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def generate_id(batchids: []):
    batchid = str(uuid.uuid4())
    if batchid in batchids:
        return generate_id()
    return batchid


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


@app.route(route="batch/{batchid}/create/file/{fileid}/{filename}", methods=["POST"])
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
@app.blob_output(
    arg_name="outputBlob",
    connection="AzureWebJobsStorage",
    path="output/{batchid}/{fileid}/{filename}",
    create_if_not_exists=True,
)
@app.queue_output(
    arg_name="textExtractionQueue",
    queue_name="text-extraction-queue",
    connection="AzureWebJobsStorage",
)
@app.cosmos_db_input(
    arg_name="batches",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="batch",
    sql_query="SELECT * FROM c",
    # partition_key="{batchid}"
)
@app.cosmos_db_output(
    arg_name="outputBatchesDB",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="batch",
    # partition_key="{batchid}"
)
def create_batch(
    req: func.HttpRequest,
    outputDB: func.Out[func.Document],
    outputBlob: func.Out[str],
    files: func.DocumentList,
    textExtractionQueue: func.Out[str],
    batches: func.DocumentList,
    outputBatchesDB: func.Out[func.Document],
) -> func.HttpResponse:
    files = req.files.getlist("files")
    if len(files) == 0:
        return func.HttpResponse(
            json.dumps({"message": "No files provided"}), status_code=400
        )
    if len(files) > 1:
        return func.HttpResponse(
            json.dumps({"message": "Only one file is allowed"}), status_code=400
        )
    file_to_upload = files[0]
    batchid = req.route_params["batchid"]
    filename = req.route_params["filename"]
    fileid = req.route_params["fileid"]
    batches_list = [dict(batch) for batch in batches]
    batchids_list = [batch["batchid"] for batch in batches_list]

    if batchid in batchids_list:
        return func.HttpResponse(
            json.dumps({"message": "Batch already exists"}), status_code=400
        )

    # outputBlob.set(file_to_upload.stream.read())

    file_obj = {
        "id": str(len(files) + 1),
        "batchid": batchid,
        "filename": filename,
        "size": file_to_upload.content_length,
        "content_type": file_to_upload.content_type,
        "filepath": f"output/{batchid}/{fileid}/{filename}",
        "extracted_text": "",
        "text_extraction_status": "pending",
        "text_extraction_message": "",
        "text_extraction_start_time": "",
        "text_extraction_end_time": "",
        "sow_extraction_status": "pending",
        "sow_extraction_message": "",
        "sow_extraction_start_time": "",
        "sow_extraction_end_time": "",
    }

    outputDB.set(func.Document.from_dict(file_obj))

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
    outputBatchesDB.set(func.Document.from_dict(new_batch_to_process))
    # logging.info("File to upload is: ", str(file_to_upload))

    # encoded_content = base64.b64encode(file_to_upload).decode("utf-8")

    # pdf_reader = PdfReader(io.BytesIO(file_to_upload.read()))
    # text = ""
    # for page in pdf_reader.pages:
    #     text += page.extract_text()

    # Compress the file content
    compressed_file = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed_file, mode='wb') as gz:
        with file_to_upload.stream as in_file:
            gz.write(in_file.read())


    # logging.info(text)
    # with (file_to_upload.stream) as in_file:
    #     encoded_file = base64.b64encode(in_file.read()).decode("utf-8")
    
    # compress file to least size

    compressed_encoded_file = base64.b64encode(compressed_file.getvalue()).decode("utf-8")


    # use pdfminer to extract text from pdf

    textExtractionQueue.set(
        json.dumps(
            {
                "batch": new_batch_to_process,
                "file_obj": file_obj,
                "bytes_file_data": compressed_encoded_file,
            }
        )
    )

    return func.HttpResponse(
        json.dumps({"message": "Batch created", "data": new_batch_to_process}),
        status_code=200,
    )


@app.route(route="batch/{batchid}/process", methods=["GET"])
@app.cosmos_db_input(
    arg_name="batches",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="batch",
    sql_query="SELECT * FROM c where c.batchid = {batchid}",
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
def process_batch(
    req: func.HttpRequest,
    batches: func.DocumentList,
    files: func.DocumentList,
) -> func.HttpResponse:
    batchid = req.route_params["batchid"]
    logging.info(f"Starting batch {batchid}")
    logging.info(batches)

    return func.HttpResponse(
        json.dumps(
            {
                "message": "Batch is being processed, please wait",
                "data": batches,
                "files": files,
            }
        ),
        status_code=200,
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
    file_obj = parse_json["file_obj"]
    bytes_file_data = parse_json["bytes_file_data"]
    file_to_extract = base64.b64decode(bytes_file_data)
    output_string  = io.StringIO()
    parser = PDFParser(file_to_extract)
    doc = PDFDocument(parser)
    rsrcmgr = PDFResourceManager()
    device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.create_pages(doc):
        interpreter.process_page(page)
    
    logging.info(
        f"Extracted text from file {file_obj['filename']} is {output_string.getvalue()}"
    )

    
    # extract text from pdf

    with open(file_obj, "wb") as in_file:
        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)
    
    logging.info(
        f"Extracted text from file {file_obj['filename']} is {output_string.getvalue()}"
    )


    # text_extraction_start_time = time.time()
    # batch["text_extraction_status"] = "processing"
    # outputDB.set(func.Document.from_dict(batch))
    # logging.info("Text extraction in progress...")
    # with io.BytesIO(file_content) as file:
    #     text = extract_text_to_fp(file, laparams=LAParams(), output_type="text")


    # filesOutputDB.set(func.Document.from_dict({**file_obj, "extracted_text": text}))
    # batch["text_extraction_status"] = "completed"
    # text_extraction_end_time = time.time()
    # batch["text_extraction_start_time"] = str(text_extraction_start_time)
    # batch["text_extraction_end_time"] = str(text_extraction_end_time)
    # outputDB.set(func.Document.from_dict(batch))
    # startSOWExtractionQueue.set(json.dumps({"batch": batch, "file": }))
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
    startSOWExtractionQueue: func.QueueMessage,
    outputDB: func.Out[func.Document],
    books: func.DocumentList,
    bookOutputDB: func.Out[func.Document],
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
