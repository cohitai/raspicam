import paramiko

#camera's sensors info.
cameras = [{"wifi":"192.168.11.115","ethernet":"10.150.180.52","pwd":"raspberry"},{"wifi":"192.168.11.119","ethernet":"10.150.180.54","pwd":"1234"}]
cam1,cam2 = cameras[0],cameras[1]

# ssh connection
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(hostname=cam1["ethernet"], username="pi" , password=cam1["pwd"])
    
except paramiko.ssh_exception.NoValidConnectionsError:
    ssh.connect(hostname=cam1["wifi"], username="pi" , password=cam1["pwd"])
except Exception: 
    raise Exception; "no route to host"
