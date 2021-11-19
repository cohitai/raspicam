import cv2
import requests
import numpy as np
from datetime import datetime
import os
import sys
import glob
from pathlib import Path
import logging
import re
import paramiko
import time
import argparse



class Camera():
    """camera control class for a raspberrypi web cam. """
    def __init__(self,ip,path_to_data_directory,port=8080):
        
        self.ip = ip #ip address of the camera
        self.port = port #port number of the camera
        self.user = 'pi'
        self.pwd = 'raspberry'
        self.id = self.ip.split('.')[-1] #serial integer for the camera, taken for the given ip x.x.x.z in the network
        self.stream_path = f'http://{self.ip}:{str(self.port)}/?action=streaming' #mjpg- streamer call
        self.path_to_data_directory = path_to_data_directory
        # create logger with 'spam_application'
        logging.getLogger(f'Raspi-application-{self.id}')
        logging.basicConfig(stream=sys.stdout, filemode='a', level=logging.DEBUG)



    def session(self, time):
        
        # ssh connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.ip, self.port, self.user , self.pwd)

        logging.debug('open-camera-id: {0}'.format(self.id))
        self._open_camera(ssh, sharpness=50, brightness=50, contrast=60, fps=2, res_x=1080, res_y=720,port=self.port)
        logging.debug('record-camera-id: {0}'.format(self.id))
        self._record_video(time, self.stream_path, self.path_to_data_directory)
        logging.debug('shutdown-camera-id: {0}'.format(self.id))
        self._shut_camera(ssh)

    def _open_camera(client, sharpness, brightness, contrast, fps, res_x, res_y, port):
    
        OPEN_CAMERA_CMD = f"mjpg_streamer -i \"input_raspicam.so -br {brightness} -co {contrast} -sh {sharpness} -x {res_x}  -y {res_y}  -fps {fps}\" -o \'output_http.so -p {port}\'"
        
        stdin, stdout, stderr = client.exec_command(OPEN_CAMERA_CMD)
        time.sleep(1)  # bug fix: AttributeError

        for i in reversed(range(10)):
            time.sleep(1)
            logging.debug(f"sleeping time..: {i}")

        return stdin, stdout, stderr

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


    def _record_video(length_secs, path_to_stream, path_to_data):
        """ function records video
        :param: length_secs: int
                path_to_stream: string
                path_to_data: string """

        r = requests.get(path_to_stream, stream=True)
        if r.status_code == 200:
            bytes_loc = bytes()
            time_start = datetime.now()
            logging.debug(f'Start recording at: {time_start}')
            for chunk in r.iter_content(chunk_size=1024):
                bytes_loc += chunk
                a = bytes_loc.find(b'\xff\xd8')  # JPEG start
                b = bytes_loc.find(b'\xff\xd9')  # JPEG end
                if a != -1 and b != -1:
                    jpg = bytes_loc[a:b + 2]  # actual image
                    bytes_loc = bytes_loc[b + 2:]  # other information
                    # decode to colored image
                    i = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    datetimeobj = datetime.now()  # get time stamp
                    cv2.imwrite(path_to_data + '/img' + str(datetimeobj) + '.jpg', i)
                    if cv2.waitKey(1) == 27 or (datetimeobj - time_start).seconds > length_secs:  # if user  hit esc
                        logging.debug('End recording.')
                        break  # exit program
        else:
            logging.error("Received unexpected status code {}".format(r.status_code))
