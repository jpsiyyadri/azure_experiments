import json
import logging

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="batch/{batchid}", methods=["DELETE"])
@app.cosmos_db_input(
    arg_name="ipBatchDocuments",
    connection="AzureCosmosDBConnectionString",
    database_name="books",
    container_name="batch",
    sql_query="SELECT * FROM c WHERE c.batchid = {batchid} and c.status != 'deleted' or not is_defined(c.status)",
)
@app.cosmos_db_output(
    arg_name="opBatchDocument",
    connection="AzureCosmosDBConnectionString",
    database_name="books",
    container_name="batch",
)
def delete_batch(req: func.HttpRequest, ipBatchDocuments: func.DocumentList, opBatchDocument: func.Out[func.Document]) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    batchid = req.route_params.get('batchid')

    batches = [doc.to_dict() for doc in ipBatchDocuments]
    if not batches:
        return func.HttpResponse(f"Batch {batchid} not found", status_code=404)

    batch = batches[0]
    batch["status"] = "deleted"
    opBatchDocument.set(func.Document.from_dict(batch))

    return func.HttpResponse(f"Batch {batchid} has been deleted", status_code=200)


@app.route(route="batches", methods=["GET"])
@app.cosmos_db_input(
    arg_name="batchDocuments",
    connection="AzureCosmosDBConnectionString",
    database_name="books",
    container_name="batch",
    sql_query="SELECT * FROM c WHERE c.status != 'deleted' or not is_defined(c.status)",
)
def get_batches(req: func.HttpRequest, batchDocuments: func.DocumentList) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    batches = [doc.to_dict() for doc in batchDocuments]
    return func.HttpResponse(json.dumps(batches), status_code=200)
