#!/usr/bin/env python
"""
Runner Pyzza Launcher Manager

RPlauncher

Runner Pyzza main script 
"""

__author__ = "Emilio Potenza"
__copyright__ = "Copyright 2011, RunnerPyzza"
__credits__ = ["Marco Galardini"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Emilio Potenza"
__email__ = "emilio.potenza@iasma.it"
__status__ = "Development"

################################################################################
# Imports

import sys
import logging
from optparse import OptionParser, OptionGroup
import socket
import time
from RunnerPyzza.Common.Protocol import iProtocol, oProtocol
from RunnerPyzza.Common.JSON import JSON
from RunnerPyzza.Common.System import System
from RunnerPyzza.LauncherManager.XMLHandler import ScriptChain
from RunnerPyzza.LauncherManager.XMLHandler import MachinesSetup
import getpass

################################################################################
# Read options

def getOptions():
    usage = "usage: python RPlauncher.py [options]"
    version="RPlauncher.py "+str(__version__)
    description=("RPlauncher.py: RunnerPyzza main script")
    parser = OptionParser(usage,version=version,description=description)
    
    group0 = OptionGroup(parser, "RPlauncher MODE")
    group0.add_option('-f', '--function', action="store", dest='function',
        default="run",
        help='Change RPlauncher mode, run|read  [run]')
    group0.add_option('-d', '--RPdaemon', action="store", dest='RPdaemon',
        default=None,
        help='RPdaemon ip location [None]')
    group0.add_option('-p', '--port', action="store", dest='port',
        default=4123,
        help='RPdaemon server port [4123]')
    parser.add_option_group(group0)

    group1 = OptionGroup(parser, "RPlauncher run")
    group1.add_option('-i', '--inputXML', action="store", dest='inXML',
        default=None,
        help='Input XML file with pipeline [None]')
    group1.add_option('-m', '--machineXML', action="store", dest='maXML',
        default=None,
        help='Input XML file with available machines [None]')
    parser.add_option_group(group1)
    
    group1b = OptionGroup(parser, "RPlauncher read")
    group1b.add_option('-j', '--job', action="store", dest='job',
        default="1",
        help='result for job number X [1]')
    parser.add_option_group(group1b)
    
    group2 = OptionGroup(parser, "Logging and Debug")
    group2.add_option('-Q', '--quiet', action="store_true", dest='quiet',
        default=False,
        help='Quiet?')
    group2.add_option('-G', '--debug', action="store_true", dest='debug',
        default=False,
        help='Debug?')
    parser.add_option_group(group2)

    return parser.parse_args()



################################################################################
# option parser
(options, args) = getOptions()

# Log setup

# create logger
# without any name, so it's root
logger = logging.getLogger()

# Set root log level
if options.quiet:
    logger.setLevel(logging.WARN)
elif options.debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

# create console handler
ch = logging.StreamHandler()
# Set log level
if options.quiet:
    ch.setLevel(logging.WARN)
elif options.debug:
    ch.setLevel(logging.DEBUG)
else:
    ch.setLevel(logging.INFO)

# create formatter for console handler
formatter = logging.Formatter('%(asctime)s - %(message)s',
                            '%H:%M:%S')
# add formatter to console handler
ch.setFormatter(formatter)

# add console handler to logger
logger.addHandler(ch)

# create file handler
fh = logging.FileHandler('RPlauncher.log')
# Set log level
# The file handler by default print all the levels but DEBUG
if options.debug:
    fh.setLevel(logging.DEBUG)
else:
    fh.setLevel(logging.INFO)
# create formatter
formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s',
                            '%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
logger.addHandler(fh)

################################################################################
# Implementation

def launcherQuit(client_socket = None, quit_msg = None, exit = True):
    '''
    Close RPlauncher and socket if available
    '''
    if client_socket:
        ##Close connection and start queue
        client_socket.send(quit_msg)
        # wait more than a little bit
        time.sleep(1)
        # close socket connection without error
        client_socket.close()
        logging.info("RPlauncher: Bye Bye!")
    if exit:
        sys.exit()

################################################################################
# Main

def main():
    logger.info('RPlauncher: starting...')
    if options.function == "run":
        # Check the arguments
        if not options.inXML:
            logger.error('Missing mandatory parameters: (-i,--inputXML)')
            logger.error('Stopping RPlauncher')
            sys.exit()
        elif not options.maXML:
            logger.error('Missing mandatory parameters: (-m,--machineXML)')
            logger.error('Stopping RPlauncher')
            sys.exit()
        elif not options.RPdaemon:
            logger.error('Missing mandatory parameters: (-d,--RPdaemon)')
            logger.error('Stopping RPlauncher')
            sys.exit()
        else:
            logger.debug('RPlauncher: mandatory parameters available.')

        logging.info("RPlauncher: reading input XML...")
        f=open(options.inXML)
        h = ScriptChain(''.join(f.readlines()))
        logging.info("RPlauncher: reading machine XML...")
        m = MachinesSetup(options.maXML)
        for i in m.getMachines():
                i.setPassword(getpass.getpass('RPlauncher: Password for machine "%s" (user %s): '%(i.name,i.getUser())))

        logging.info("RPlauncher: open cominication with daemon...")
        # Client comunication
        iPP = iProtocol()
        oPP = oProtocol()
        ok = System("ok")
        quit = System("quit")
        result = System("result")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((options.RPdaemon, int(options.port)))
        for prg in h.getPrograms():
            #send command
            client_socket.send(oPP.interpretate(prg))
            #wait answers
            server_data = client_socket.recv(1024)
            if iPP.interpretate(server_data).body != 'ok':
                logger.error('Program comunication is not "ok" ...')
                logger.error(iPP.interpretate(server_data))
                logger.error('Stopping RPlauncher...')
                launcherQuit(client_socket, oPP.interpretate(quit))
            #wait a little bit
            time.sleep(0.1)

        for mch in m.getMachines():
            #send command
            client_socket.send(oPP.interpretate(mch))
            #wait answers
            server_data = client_socket.recv(1024)
            if iPP.interpretate(server_data).body != 'ok':
                logger.error('Machine comunication is not "ok" ...')
                logger.error(iPP.interpretate(server_data))
                logger.error('Stopping RPlauncher...')
                launcherQuit(client_socket, oPP.interpretate(quit))
            #wait a little bit
            time.sleep(0.1)
        
        logging.info("Cominication done! You may ask for results")
        launcherQuit(client_socket, oPP.interpretate(quit))
    
    ############################################################
    if options.function == "read":
        logging.info("Results:")
        logging.info("RPlauncher: open cominication with daemon...")
        # Client comunication
        iPP = iProtocol()
        oPP = oProtocol()
        ok = System("ok")
        quit = System("quit")
        result = System("result")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((options.RPdaemon, int(options.port)))
        client_socket.send(oPP.interpretate(result))



        server_data = client_socket.recv(1024)
        if iPP.interpretate(server_data).body != 'ok':
            logger.error('Machine comunication is not "ok" ...')
            logger.error(iPP.interpretate(server_data))
            logger.error('Stopping RPlauncher...')
            launcherQuit(client_socket, oPP.interpretate(quit))
        #wait a little bit
        time.sleep(0.1)

        client_socket.send(oPP.interpretate(System(options.job)))
        
        iPP=iProtocol()
        server_data = client_socket.recv(1024)
        logging.info("Results of job %s"%(options.job))
        print iPP.interpretate(server_data)
        time.sleep(0.1)

        launcherQuit(client_socket, oPP.interpretate(quit))

if __name__ == '__main__':
    main()







