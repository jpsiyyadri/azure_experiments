import json
import logging

import azure.functions as func
import pandas as pd
import requests

from db import SessionLocal
from models import Person

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


account_name = "storageforedd"
account_key = "rCOAwcUX98YcL4GwYzad7PPESv/OIqNb6M5SpytMdH6zyuju3oxD6lbqKYEAflqkuxcXFdpMziPL+AStg2TDuQ=="


connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"


@app.function_name("cool_function")
@app.route(
        route="http_trigger",
        methods=["GET"],
        auth_level=func.AuthLevel.ANONYMOUS
    )
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    # time.sleep(240)
    df = pd.DataFrame(
        {
            "A": [1, 2, 3, 4],
            "B": [5, 6, 7, 8],
            "C": [9, 10, 11, 12],
        }
    )

    return func.HttpResponse(
        body=df.to_json(),
        status_code=200,
        mimetype="application/json",
    )


@app.function_name("read_external_api")
@app.route(
        route="read_external_api",
        methods=["GET"],
        auth_level=func.AuthLevel.ANONYMOUS
    )
def read_external_api(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    response = requests.get("https://jsonplaceholder.typicode.com/todos/1")
    data = response.json()

    return func.HttpResponse(
        body=json.dumps(data),
        status_code=200,
        mimetype="application/json",
    )


# create a cosmos db on http trigger
@app.function_name("create_user")
@app.route(
        route="create_user",
        methods=["GET"],
        auth_level=func.AuthLevel.ANONYMOUS
    )
def create_user(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    person = Person(name="Jacerys", age=3, email="abc@hi.com")

    with SessionLocal() as session:
        session.add(person)
        session.commit()
        session.refresh(person)
    
    logging.info(person)
    logging.info("User created successfully!!!")

    return func.HttpResponse(
        body=json.dumps(person),
        status_code=200,
        mimetype="application/json",
    )
