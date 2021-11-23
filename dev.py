import raspicam as rp
import multiprocessing as mlt
import time

import os, uuid
import glob
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__

os.environ['AZURE_STORAGE_CONNECTION_STRING'] = 'DefaultEndpointsProtocol=https;AccountName=blobsdb;AccountKey=tJK43kihAcaeZMjcegWFcyg8tsFmOr9f2Kn8q6NUinVSJW5O3jymYbjaiGBjmx8Ibq5LsBVPcABvYeV+tUCPnQ==;EndpointSuffix=core.windows.net'
connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

# Create the BlobServiceClient object which will be used to create a container client
blob_service_client = BlobServiceClient.from_connection_string(connect_str)


#cameras sensor info.
cameras = [{"ip":"192.168.11.115","pwd":"raspberry"},{"ip":"192.168.11.119","pwd":"1234"}]

#local dir (data)
local_path = "./data"

def cam_run(camera_info):
    cam = rp.Camera(camera_info["ip"], local_path, camera_info["pwd"])
    cam.session(3)

while True:
    start = time.perf_counter()

    # Create a unique name for the container
    #container_name = str('raspi' + str(time)).replace(".","")
    container_name=str(uuid.uuid4())
    print("Containers Name: ", container_name)


    # Create the container
    container_client = blob_service_client.create_container(container_name)

    processes=[]

    for cam_d in cameras:
        p=mlt.Process(target=cam_run,args=(cam_d,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    finish=time.perf_counter()

    # commit data to azure
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

        os.remove(file)

    print("go to sleep,",finish)
    time.sleep(1000)
