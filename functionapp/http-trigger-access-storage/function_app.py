import logging

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="ReadData")
def read_data(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )


@app.route(route="ReadDataFromBlob/{name}")
@app.blob_input(
    arg_name="input_blob",
    path='filecontainer/{name}',
    connection="AzureWebJobsStorage"
    )
@app.blob_output(
    arg_name="output_blob",
    path='outputfiles/{name}',
    connection="AzureWebJobsStorage",

    )
def read_and_write_data_using_blob(
            req: func.HttpRequest, 
            input_blob: func.InputStream,
            output_blob: func.Out[str]

        ) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    if (not input_blob):
        return func.HttpResponse(f"File Not Found", status_code=404)

    blobdata = input_blob.read().decode('utf-8')

    # write data to output blob
    output_blob.set(blobdata)

    return func.HttpResponse(f"Hello, {blobdata}. This HTTP triggered function executed successfully.")
