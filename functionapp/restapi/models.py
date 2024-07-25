from typing import List

from pydantic import BaseModel

from database import Database

connection_uri = "https://cosmosforapi.documents.azure.com:443/"
access_key = "09ViP0Utip2OXipBM9jC3EpZpTOXeZDUEBpDd3IUIVSOqQs3ipgp2LmlVyNy9grIPF7HttXnR5C6ACDbtl6ceA=="

database_connection = Database(connection_uri, access_key, "books", "book")
print(database_connection.read_items())


class Book(BaseModel):
    title: str
    author: str
    publisher: str
    id: str
    batchid: str
    
    def __init__(self, title, author, publisher, batchid):
        self.id = str(len(database_connection.read_items()) + 1)
        self.title = title
        self.author = author
        self.publisher = publisher
        self.batchid = batchid

    def save(self):
        database_connection.create_item(
            self.dict()
        )

    def delete(self):
        database_connection.delete_item(self.title)

    def update(self):
        database_connection.update_item(self.title, self.dict())

    def __str__(self):
        return f'{self.title} by {self.author}'

