from azure.cosmos import CosmosClient, PartitionKey


class Database:
    def __init__(self, connection_uri=None, access_key=None, database_name=None, container_name=None):
        self.client = CosmosClient(
                connection_uri,
                credential=access_key
            )
        self.database = self.client.create_database_if_not_exists(database_name)
        self.container = self.database.create_container_if_not_exists(container_name, partition_key=PartitionKey(path="/batchid"))

    def create_item(self, item):
        self.container.create_item(body=item)

    def read_items(self):
        items = list(self.container.read_all_items())
        return items

    def read_item(self, item_id, partition_key):
        item = self.container.read_item(item_id, partition_key=partition_key)
        return item

    def update_item(self, item_id, item):
        self.container.upsert_item(item_id, item)

    def delete_item(self, item_id):
        self.container.delete_item(item_id)

    def query_items(self, query):
        items = list(self.container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        return items


if __name__ == "__main__":
    connection_uri = "https://cosmosforapi.documents.azure.com:443/"
    access_key = "09ViP0Utip2OXipBM9jC3EpZpTOXeZDUEBpDd3IUIVSOqQs3ipgp2LmlVyNy9grIPF7HttXnR5C6ACDbtl6ceA=="

    database_connection = Database(connection_uri, access_key, "books", "book")
    # print(database_connection.read_items())
    # database_connection.create_item({"id": "1", "batchid": "2", "title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "publisher": "Scribner"})
    # print(database_connection.read_items())
    print(
        database_connection.read_item("1", "2")
    )
