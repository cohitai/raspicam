import cv2
import requests
import numpy as np
from datetime import datetime
import sys
import logging
import re
import paramiko
import time

class Camera():
    """camera control class for a raspberrypi web cam. """
    def __init__(self,camera_info,path_to_data_directory):
        
        self.wifi = camera_info["wifi"] #camera´s wifi address
        self.ethernet = camera_info["ethernet"] #camera´s ethernet address
        self.user = 'pi'
        self.pwd = camera_info["pwd"]
        self.path_to_data_directory = path_to_data_directory
        self.id = None
        self.stream_path_ = None
        
        # create logger with 'spam_application'
        logging.getLogger(f'Raspi-application')
        logging.basicConfig(stream=sys.stdout, filemode='a', level=logging.DEBUG)

    def session(self, time, params):
        
        # ssh connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        #ethernet first, then wifi.
        try:
            ssh.connect(hostname=self.ethernet, username=self.user , password=self.pwd)
            self.stream_path = f'http://{self.ethernet}:{str(params["port"])}/?action=streaming'
            self.id = str(self.ethernet.split('.')[-1]) #serial camera identifier
        except paramiko.ssh_exception.NoValidConnectionsError:
            ssh.connect(hostname=self.wifi, username=self.user , password=self.pwd)
            self.stream_path = f'http://{self.wifi}:{str(params["port"])}/?action=streaming'
            self.id = str(self.wifi.split('.')[-1]) #serial camera identifier
        except Exception: 
            raise Exception; "no route to host"

        #camera record session
        logging.debug('open-camera-id: {0}'.format(self.id))
        self._open_camera(ssh, params)
        logging.debug('record-camera-id: {0}'.format(self.id))
        self._record_video(time, self.stream_path, self.path_to_data_directory)
        logging.debug('shutdown-camera-id: {0}'.format(self.id))
        self._shut_camera(ssh)

    @staticmethod
    def _open_camera(client, params):
        
        port, sharpness, brightness, contrast, fps, res_x, res_y = params.values()
        OPEN_CAMERA_CMD = f"mjpg_streamer -i \"input_raspicam.so -br {brightness} -co {contrast} -sh {sharpness} -x {res_x}  -y {res_y}  -fps {fps}\" -o \'output_http.so -p {port}\'"
        
        stdin, stdout, stderr = client.exec_command(OPEN_CAMERA_CMD)
        time.sleep(1)  # bug fix: AttributeError

        for i in reversed(range(10)):
            time.sleep(1)
            logging.debug(f"sleeping time..: {i}")

        return stdin, stdout, stderr
    
    @staticmethod
    def _shut_camera(client):

        """SSH script to end broadcasting on the remote host"""
        stdin, stdout, stderr = client.exec_command("ps aux")
        time.sleep(1)  # bug fix: AttributeError
        data = stdout.readlines()  # retrieve processes output.
        for line in data:
            if line.find('mjpg_streamer') != -1:
                process_to_kill = re.findall('\d+', line)[0]
                stdin, stdout, stderr = client.exec_command(f"kill {process_to_kill}")  # execute process.
                time.sleep(1)  # bug fix (AttributeError)
                return stdin, stdout, stderr

    
    def _record_video(self,length_secs, path_to_stream, path_to_data):
        """ function records video
        :param: length_secs: int
                path_to_stream: string
                path_to_data: string """

        r = requests.get(path_to_stream, stream=True)
        if r.status_code == 200:
            bytes_loc=bytes()
            time_start=datetime.now()
            logging.debug(f'Start recording at: {time_start}')
            for chunk in r.iter_content(chunk_size=1024):
                bytes_loc+=chunk
                a=bytes_loc.find(b'\xff\xd8')  # JPEG start
                b=bytes_loc.find(b'\xff\xd9')  # JPEG end
                if a != -1 and b != -1:
                    jpg=bytes_loc[a:b + 2]  # actual image
                    bytes_loc=bytes_loc[b + 2:]  # other information
                    # decode to colored image
                    i=cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    datetimeobj=datetime.now()  # get time stamp
                    img_identifier=str((datetimeobj-time_start).seconds)+"-"+str((datetimeobj-time_start).microseconds)[:2]
                    img_name=path_to_data + "/" + self.id + 'img' + img_identifier+'.jpg'
                    cv2.imwrite(img_name, i)
                    if cv2.waitKey(1) == 27 or (datetimeobj - time_start).seconds > length_secs:  # if user  hit esc
                        logging.debug('End recording.')
                        break  # exit program
        else:
            logging.error("Received unexpected status code {}".format(r.status_code))
