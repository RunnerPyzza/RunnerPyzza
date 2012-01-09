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
from RunnerPyzza.ClientCommon.PyzzaTalk import OrderPyzza, OvenPyzza, CheckPyzza
from RunnerPyzza.Common.JSON import JSON
from RunnerPyzza.Common.Protocol import iProtocol, oProtocol
from RunnerPyzza.Common.System import System
from RunnerPyzza.LauncherManager.XMLHandler import MachinesSetup, ScriptChain
from optparse import OptionParser, OptionGroup
import getpass
import logging
import socket
import sys
import time

################################################################################
# Read options

def getOptions():
    usage = "usage: python RPlauncher.py [options]"
    version="RPlauncher.py "+str(__version__)
    description=("RPlauncher.py: RunnerPyzza main script")
    parser = OptionParser(usage,version=version,description=description)
    
    group0 = OptionGroup(parser, "RPlauncher MODE")
    group0.add_option('-f', '--function', action="store", dest='function',
        default="init",
        help='Change RPlauncher mode, init|start|status|results|clean  [init]')
    group0.add_option('-d', '--RPdaemon', action="store", dest='RPdaemon',
        default=None,
        help='RPdaemon ip location [None]')
    group0.add_option('-p', '--port', action="store", dest='port',
        default=4123,
        help='RPdaemon server port [4123]')
    parser.add_option_group(group0)

    group1 = OptionGroup(parser, "RPlauncher init")
    group1.add_option('-i', '--inputXML', action="store", dest='inXML',
        default=None,
        help='Input XML file with pipeline [None]')
    group1.add_option('-m', '--machineXML', action="store", dest='maXML',
        default=None,
        help='Input XML file with available machines [None]')
    parser.add_option_group(group1)
    
    group1a = OptionGroup(parser, "RPlauncher start|status|results|clean")
    group1a.add_option('-j', '--jobID', action="store", dest='jobID',
        default=None,
        help='JobID [None]')
    parser.add_option_group(group1a)
    
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
    if options.function == "init":
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
        order = OrderPyzza(options.RPdaemon, options.port, machines = m.getMachines(), programs = h.getPrograms(),
                 tag = 'Margherita', local = False)
        if not order.launchOrder():
            logging.warning('Pyzza not ordered!')
            return
        else:
            logging.warning('Pyzza ordered with id %s'%order.jobID)
        
    elif options.function == 'start':
        if not options.RPdaemon or not options.jobID:
            logger.error('Missing mandatory parameters')
            logger.error('Stopping RPlauncher')
            sys.exit()
        logging.info('Let\'s put the pyzza in the oven!')
        ovenizer = OvenPyzza(options.RPdaemon, options.port, options.jobID)
        if not ovenizer.putInTheOven():
            logging.warning('The oven is cold! Could not cook %s'%options.jobID)
            return
        else:
            logging.warning('Pyzza with id %s is in the oven!'%options.jobID)
     
    elif options.function == 'status':
        if not options.RPdaemon or not options.jobID:
            logger.error('Missing mandatory parameters')
            logger.error('Stopping RPlauncher')
            sys.exit()
        logging.info('Let\'s check if the pyzza is ready!')
        checker = CheckPyzza(options.RPdaemon, options.port, options.jobID)
        if not checker.checkTheOven():
            logging.warning('Could not find the pyzza! %s'%options.jobID)
            return
        else:
            if checker.isReady():
                logging.warning('The Pyzza with id %s is ready!'%options.jobID)
            elif checker.isCooking():
                logging.warning('The Pyzza with id %s is still in the oven!'%options.jobID)
                logging.warning('%d slices cooked!'%(int(checker.getLastSlice()[0])))
            elif checker.isWaiting():
                logging.warning('The oven is still cold! Waiting to cook %s'%options.jobID)
            elif checker.isBurned():
                logging.warning('The Pyzza with id %s is burned!'%options.jobID)
                logging.warning('Problematic slices:')
                for err in checker.inspectErrors():
                    logging.warning('Slice %d, Ingredients %s, Return code %d'%(int(err[0]),err[1],int(err[2])))

if __name__ == '__main__':
    main()







