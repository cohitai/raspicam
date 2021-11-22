import os, uuid
import glob
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__

os.environ['AZURE_STORAGE_CONNECTION_STRING'] = 'DefaultEndpointsProtocol=https;AccountName=blobsdb;AccountKey=tJK43kihAcaeZMjcegWFcyg8tsFmOr9f2Kn8q6NUinVSJW5O3jymYbjaiGBjmx8Ibq5LsBVPcABvYeV+tUCPnQ==;EndpointSuffix=core.windows.net'
connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

# Create the BlobServiceClient object which will be used to create a container client
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

# Create a unique name for the container
container_name = str(uuid.uuid4())
print("Containers Name: ", container_name)

# Create the container
container_client = blob_service_client.create_container(container_name)

# Create a local directory to hold blob data
local_path = "./data"

for file in glob.glob("./data/*.jpg"):
    # Create a file in the local data directory to upload and download
    local_file_name = file.split("/")[-1]
    upload_file_path = os.path.join(local_path, local_file_name)

    # Create a blob client using the local file name as the name for the blob
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_file_name)

    print("\nUploading to Azure Storage as blob:\n\t" + local_file_name)

    # Upload the created file
    with open(upload_file_path, "rb") as data:
        blob_client.upload_blob(data)