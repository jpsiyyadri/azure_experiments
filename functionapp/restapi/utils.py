import uuid

from database import Database

connection_uri = "https://cosmosforapi.documents.azure.com:443/"
access_key = "09ViP0Utip2OXipBM9jC3EpZpTOXeZDUEBpDd3IUIVSOqQs3ipgp2LmlVyNy9grIPF7HttXnR5C6ACDbtl6ceA=="

database_connection = Database(connection_uri, access_key, "books", "book")


def generate_id():
    """
        - generate batchid which is unique
        - check if the batchid is already present in the database
        - return batchid
    """
    batchid = str(uuid.uuid4())
    items = database_connection.read_items()
    batchids = [item["batchid"] for item in items]
    if batchid in batchids:
        return generate_id()
    return batchid
