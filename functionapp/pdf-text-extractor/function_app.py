

import logging
import uuid

# import azure.durable_functions as dur_func
import azure.functions as func
import pandas as pd

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="hello", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def hello(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")
    return func.HttpResponse("Hello, World!")


@app.route(
        route="upload-txt/",
        methods=["POST"],
        auth_level=func.AuthLevel.ANONYMOUS
    )
@app.blob_output(
    arg_name="outputBlob",
    path=f"output/file-{str(uuid.uuid4())}.txt",
    connection="AzureWebJobsStorage",
)
def upload(req: func.HttpRequest, outputBlob: func.Out[str]) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")
    file = req.files["file"]
    file.save("file.txt")
    outputBlob.set(open("file.txt", "rb").read())
    keys = outputBlob
    return func.HttpResponse("File uploaded successfully, keys are: " + str(keys))


@app.blob_trigger(
    arg_name="uploadedBlob",
    path="output",
    connection="AzureWebJobsStorage",
)
def blob_trigger(uploadedBlob: func.InputStream) -> None:
    logging.info(f"Blob trigger function processed blob \n"
                 f"Name: {uploadedBlob.name}\n"
                 f"Blob Size: {uploadedBlob.length} bytes")


@app.route(
        route="sampledata/",
        methods=["GET"],
        auth_level=func.AuthLevel.ANONYMOUS
    )
def sample_data(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    data = {
        "Name": ["John", "Anna", "Peter", "Linda"],
        "Location": ["New York", "Paris", "Berlin", "London"],
        "Age": [24, 13, 53, 33]
    }

    df = pd.DataFrame(data)
    return func.HttpResponse(df.to_json())
