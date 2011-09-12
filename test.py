import paramiko
import select
from getpass import getpass
import logging
logging.warning('ciao')
client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('bazzilab', 
          username='mgalardini', 
          password=getpass('Dammi la password: '))
transport = client.get_transport()
channel = transport.open_session()
channel.exec_command('echo "start";sleep 1;echo "ciao" >&2;sleep 1;echo "done"')
logging.warning('ciao')
while True:
    if channel.recv_ready():
    	print channel.recv(1024).strip()
    if channel.recv_stderr_ready():
    	print channel.recv_stderr(1024).strip()
    if channel.closed:
    	break
