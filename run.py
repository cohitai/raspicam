import raspicam as rp
import multiprocessing as mlt
import time
from datetime import datetime
import os,sys
import glob
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__
import logging

# create logger with 'spam_application'
logging.getLogger(f'Raspi-application')
logging.basicConfig(stream=sys.stdout, filemode='a', level=logging.DEBUG)

# Docs

# Azure connecting info.
os.environ['AZURE_STORAGE_CONNECTION_STRING'] = 'DefaultEndpointsProtocol=https;AccountName=blobsdb;AccountKey=tJK43kihAcaeZMjcegWFcyg8tsFmOr9f2Kn8q6NUinVSJW5O3jymYbjaiGBjmx8Ibq5LsBVPcABvYeV+tUCPnQ==;EndpointSuffix=core.windows.net'
connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
# Create the BlobServiceClient object which will be used to create a container client.
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

#list containers
#next(blob_service_client.list_containers())

# Camera's sensors info.
# very good results with sharpness:50, brightness:50, contrast:60, fps:3, res=1080,720, RECORDING_TIME=29
cameras = [{"wifi":"192.168.11.115","ethernet":"10.150.180.52","pwd":"1234"}, {"wifi":"192.168.11.136","ethernet":"10.150.180.56","pwd":"raspberry"}]
params = {"port":8080, "sharpness":50, "brightness":50, "contrast":60, "fps":3, "res_x":1080, "res_y":720}
RECORDING_TIME=29
# local dir for saving images.
local_path = "./data"

# function to run with MultiProcessing.
def cam_run(camera_info):
    cam = rp.Camera(camera_info,local_path)
    cam.session(RECORDING_TIME, params)

def main():
    while True:
        start = time.perf_counter()
        # Create a unique name for the container.
        #container_name=str(uuid.uuid4())
        container_name=str(datetime.now().timestamp()).replace(".","-")
        logging.info(f"Containers Name: {container_name}")

        # Create the container.
        container_client = blob_service_client.create_container(container_name)

        # Run cameras on parallel processes.
        processes=[]
        for cam in cameras:
            p=mlt.Process(target=cam_run,args=(cam,))
            p.start()
            processes.append(p)
        for p in processes:
            p.join()

        finish=time.perf_counter()

        # Commit data to azure
        for img in glob.glob("./data/*.jpg"):
            # Create a img in the local data directory to upload and download.
            local_img_name = img.split("/")[-1]
            upload_img_path = os.path.join(local_path, local_img_name)

            # Create a blob client using the local file name as the name for the blob.
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_img_name)

            logging.info(f"\nUploading to Azure Storage as blob:\n\t{local_img_name}")

            # Upload the created img.
            with open(upload_img_path, "rb") as data:
                blob_client.upload_blob(data)

            # Deletes img from local.
            os.remove(img)

        logging.info(f"go to sleep, {finish}")
        time.sleep(3600)

if __name__ == "__main__":
    main()
