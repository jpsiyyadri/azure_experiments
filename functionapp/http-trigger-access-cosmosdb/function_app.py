import json
import logging

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="access_cosmos/")
@app.cosmos_db_input(
    arg_name="documents",
    connection="AzureWebJobCosmosDBConnectionString",
    database_name="SampleDB",
    container_name="SampleContainer",
)
@app.cosmos_db_output(
    arg_name="outputs",
    connection="AzureWebJobCosmosDBConnectionString",
    database_name="SampleDB",
    container_name="SampleContainerOutput",
    create_if_not_exists=True,
    partition_key="/id",
)
def access_cosmos(req: func.HttpRequest, documents: func.DocumentList, outputs: func.Out[func.DocumentList]) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    if not documents:
        return func.HttpResponse(
            "No documents found",
            status_code=404
        )
    
    for doc in documents:
        doc["processed"] = True

    outputs.set(documents)

    return func.HttpResponse(
        body=json.dumps([doc.to_json() for doc in documents]),
        status_code=200
    )
