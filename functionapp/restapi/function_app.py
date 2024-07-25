import base64
import io
import json  # to handle output as json
import logging
import time
import uuid

import azure.functions as func

from sow_and_mappings_bp import openai_blueprint


def install(package):
    from importlib import import_module

    try:
        import_module(package)
    except ImportError:
        import subprocess

        subprocess.check_call(["python", "-m", "pip", "-q", "install", package])


for package in ["langchain", "langchain-openai", "pdfminer.six"]:
    install(package)


from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
app.register_functions(openai_blueprint)

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


@app.route(route="batch/{batchid}", methods=["POST"])
@app.cosmos_db_output(
    arg_name="outputDB",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="files",
)
@app.cosmos_db_input(
    arg_name="ipFilesDocuments",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="files",
    sql_query="SELECT * FROM c",
)
@app.blob_output(
    arg_name="outputBlob",
    connection="AzureWebJobsStorage",
    path="output/{batchid}/*",
    create_if_not_exists=True,
)
@app.queue_output(
    arg_name="sowExtractionQueue",
    queue_name="sow-extraction-queue",
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
    ipFilesDocuments: func.DocumentList,
    sowExtractionQueue: func.Out[str],
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
    # filename = req.route_params["filename"]
    filename = file_to_upload.filename
    # fileid = req.route_params["fileid"]
    fileid = 1
    batches_list = [dict(batch) for batch in batches]
    batchids_list = [batch["batchid"] for batch in batches_list]

    if batchid in batchids_list:
        return func.HttpResponse(
            json.dumps({"message": "Batch already exists"}), status_code=400
        )

    try:
        output_string  = io.StringIO()
        with io.BytesIO(file_to_upload.read()) as in_file:
            parser = PDFParser(in_file)
            doc = PDFDocument(parser)
            rsrcmgr = PDFResourceManager()
            device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.create_pages(doc):
                interpreter.process_page(page)
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"message": str(e)}), status_code=500
        )
    
    outputBlob.set(file_to_upload.stream.read())

    new_file_row_id = str(len(ipFilesDocuments) + 1)
    file_obj = {
        "id": new_file_row_id,
        "batchid": batchid,
        "filename": filename,
        "size": file_to_upload.content_length,
        "content_type": file_to_upload.content_type,
        "filepath": f"output/{batchid}/{fileid}/{filename}",
        "extracted_text": output_string.getvalue(),
        "extracted_sow": "",
        "text_extraction_status": "completed",
        "text_extraction_message": "",
        "text_extraction_start_time": "",
        "text_extraction_end_time": "",
        "sow_extraction_status": "pending",
        "sow_extraction_message": "",
        "sow_extraction_start_time": "",
        "sow_extraction_end_time": "",
    }

    outputDB.set(func.Document.from_dict(file_obj))
    new_batch_row_id = str(len(batches_list) + 1)
    new_batch_to_process = {
        "id": new_batch_row_id,
        "batchid": batchid,
        "files_count": len(files),
        "text_extraction_status": "completed",
        "text_extraction_message": "",
        "text_extraction_start_time": "",
        "text_extraction_end_time": "",
        "sow_extraction_status": "pending",
        "sow_extraction_message": "",
        "sow_extraction_start_time": "",
        "sow_extraction_end_time": "",
    }
    outputBatchesDB.set(func.Document.from_dict(new_batch_to_process))

    sowExtractionQueue.set(json.dumps({"batchid": batchid, "batch_row_id": new_batch_row_id, "file_row_id": new_file_row_id}))

    return func.HttpResponse(
        json.dumps({"message": "Batch created", "data": new_batch_to_process}),
        status_code=200,
    )


@app.route(route="batch/{batchid}", methods=["GET"])
@app.cosmos_db_input(
    arg_name="ipBatchDocuments",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="batch",
    sql_query="SELECT * FROM c where c.batchid = {batchid}",
    # partition_key="{batchid}"
)
def get_batch(
    req: func.HttpRequest,
    ipBatchDocuments: func.DocumentList,
) -> func.HttpResponse:
    # deserialize batch document
    batches = [dict(batch) for batch in ipBatchDocuments]

    return func.HttpResponse(
        json.dumps(
            {
                "message": "success",
                "data": batches,
                # "files": files,
            }
        ),
        status_code=200,
        mimetype="application/json",
    )


@app.route(route="batch/{batchid}/file/{fileid}", methods=["GET"])
@app.cosmos_db_input(
    arg_name="ipFilesDocuments",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="files",
    sql_query="SELECT * FROM c where c.batchid = {batchid} and c.id = {fileid}",
    # partition_key="{batchid}"
)
def get_file_data(
    req: func.HttpRequest,
    ipFilesDocuments: func.DocumentList,
) -> func.HttpResponse:
    # deserialize batch document
    files = [dict(file) for file in ipFilesDocuments]

    if len(files) == 0:
        return func.HttpResponse(
            json.dumps({"message": "No file found", "data": []}), status_code=404
        )

    file_obj = files[0]
    
    # extract id, batchid, filename, size, content_type, extracted_text,
    # extracted_sow, text_extraction_status, sow_extraction_status,
    # total mappings count, mappings completed count, mappings pending count
    mappings = file_obj.get("mappings", [])
    mappings_completed = len([mapping for mapping in mappings if mapping["status"] == "completed"])
    mappings_pending = len([mapping for mapping in mappings if mapping["status"] == "pending"])
    mappings_failed = len([mapping for mapping in mappings if mapping["status"] == "failed"])
    mappings_total = len(mappings)

    response = {
        "id": file_obj["id"],
        "batchid": file_obj["batchid"],
        "filepath": file_obj["filepath"],
        "content_type": file_obj["content_type"],
        "extracted_text": file_obj["extracted_text"],
        "extracted_sow": file_obj["extracted_sow"],
        "text_extraction_status": file_obj["text_extraction_status"],
        "sow_extraction_status": file_obj["sow_extraction_status"],
        "total_mappings_count": mappings_total,
        "mappings_completed_count": mappings_completed,
        "mappings_pending_count": mappings_pending,
        "mappings_failed_count": mappings_failed,
    }

    return func.HttpResponse(
        json.dumps(
            {
                "message": "success",
                "data": response,
            }
        ),
        status_code=200,
        mimetype="application/json",
    )

