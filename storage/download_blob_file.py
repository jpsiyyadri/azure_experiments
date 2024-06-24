import os

from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

# Define the Azure Storage account name and key
account_name = os.getenv("STORAGE_ACCOUNT_NAME")
account_key = os.getenv("STORAGE_ACCOUNT_KEY")

print(account_name)
print(account_key)

# Define the connection string to authenticate the service account
connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"

blob_service_client = BlobServiceClient.from_connection_string(connection_string)

container_name = "csvfiles"
blob_name = "alzheimers_disease_data.csv"

container_client = blob_service_client.get_container_client(container_name)
blob_client = container_client.get_blob_client(blob_name)

# Download the blob file to the local file system
with open("downloaded_alzheimers_disease_data.csv", "wb") as my_blob:
    download_stream = blob_client.download_blob()
    my_blob.write(download_stream.readall())

print("Blob file downloaded successfully!")
