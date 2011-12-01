import sys
import logging
import socket
import sys
import time

# Variables Server - Client comunication
port = 4123
host_server = raw_input("Server IP ??? =")

logger = logging.getLogger()

logger.setLevel(logging.DEBUG)

# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter for console handler
formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s',
                            '%H:%M:%S')
# add formatter to console handler
ch.setFormatter(formatter)

# add console handler to logger
logger.addHandler(ch)

# create file handler
fh = logging.FileHandler('Test.log')
# Set log level
# The file handler by default print all the levels but DEBUG
fh.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
                            '%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
logger.addHandler(fh)

from Common.JSON import JSON
msgHandler = JSON()
from LauncherManager.XMLHandler import ScriptChain

f=open(sys.argv[1])
h = ScriptChain(''.join(f.readlines()))
#h = ScriptChain('<?xml version="1.0" encoding="UTF-8"?>\n\n<scriptChain xmlns="RunnerPyzza"\n  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n  xsi:schemaLocation="RunnerPyzza Launcher.xsd">\n  <program>\n    <main>\n      <name>CONTIGuator</name>\n      <baseCommand>python CONTIGuator.py</baseCommand>\n      <order>2</order>\n    </main>\n    <option>\n      <alias>-c</alias>\n      <value>contigs.fna</value>\n      <separator> </separator>\n      <delimiter></delimiter>\n    </option>\n    <option>\n      <alias>-r</alias>\n      <value>references.fna</value>\n      <separator> </separator>\n      <delimiter></delimiter>\n    </option>\n    <cpu>\n      <numCPU>2</numCPU>\n      <kind>prefix</kind>\n      <cmdCPU>mpirun -n</cmdCPU>\n      <separator> </separator>\n      <delimiter></delimiter>\n    </cpu>\n  </program>\n  <program>\n    <main>\n      <name>List directory</name>\n      <baseCommand>ls</baseCommand>\n      <order>1</order>\n    </main>\n    <option>\n      <alias></alias>\n      <value>/home/</value>\n      <separator></separator>\n      <delimiter></delimiter>\n    </option>\n  </program>\n</scriptChain>\n')
#h = ScriptChain('<?xml version="1.0" encoding="UTF-8"?>')
print str(h)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((host_server, port))

for prg in h.getPrograms():
    msg = msgHandler.encode(prg.msg())
    #send command
    client_socket.send(msg)
    server_data = client_socket.recv(1024)
    print server_data
    time.sleep(0.3)
   
from LauncherManager.XMLHandler import MachinesSetup
import getpass
m = MachinesSetup(sys.argv[2])
for i in m.getMachines():
	i.setPassword(getpass.getpass('Password for machine "%s" (user %s): '%(i.name,i.getUser())))
print str(m)
for mch in m.getMachines():
    msg = msgHandler.encode(mch.msg())
    #send command
    client_socket.send(msg)
    server_data = client_socket.recv(1024)
    print server_data
    time.sleep(0.3)

client_socket.send('{"values": {"msg" : "quit"}, "type" : "system"}')
time.sleep(1)
client_socket.close()
print "done"
