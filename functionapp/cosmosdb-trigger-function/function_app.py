import logging

import azure.functions as func

app = func.FunctionApp()


@app.cosmos_db_trigger(arg_name="doc", container_name="SampleContainer",
                        database_name="SampleDB", connection="cosmosfornosql_DOCUMENTDB",
                        create_lease_container_if_not_exists=True, lease_container_name="leases")
@app.cosmos_db_output(arg_name="outputDocument", database_name="SampleDB", container_name="OutputContainer",
                        connection="cosmosfornosql_DOCUMENTDB")
def cosmosdb_trigger(doc: func.DocumentList):
    logging.info('Python CosmosDB triggered.')

    if doc:
        logging.info(f'Document id: {doc[0]["id"]}')
        outputDocument.set(
            {
                "OpID": doc[0]["id"],
                "name": "control",
            }
        )
    else:
        logging.info('No changes')

