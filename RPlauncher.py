#!/usr/bin/env python
"""
Runner Pyzza Launcher Manager

RPlauncher

Runner Pyzza main script 
"""
from RunnerPyzza import __version__
from RunnerPyzza.ClientCommon.PyzzaTalk import OrderPyzza, OvenPyzza, CheckPyzza, \
    EatPyzza
from RunnerPyzza.LauncherManager.XMLHandler import MachinesSetup, ScriptChain
import argparse
import getpass
import logging
import sys
import time

__author__ = "Emilio Potenza"
__credits__ = ["Marco Galardini"]

################################################################################
# Log

# Log setup
# create logger
# without any name, so it's root
logger = logging.getLogger()

################################################################################
# Methods

def init(options):
    logger.info("Reading inputs")
    f=open(options.scriptChain)
    h = ScriptChain(''.join(f.readlines()))
    logger.info("RPlauncher: reading machine XML...")
    m = MachinesSetup(options.machines)
    for i in m.getMachines():
            i.setPassword(getpass.getpass(
                          'Password for machine "%s" (user %s): '%
                          (i.name,i.getUser())))

    logger.info("Open cominication with daemon...")
    order = OrderPyzza(options.host, options.port,
            machines = m.getMachines(), programs = h.getPrograms(),
            tag = 'Margherita', local = False)
    if not order.launchOrder():
        logger.warning('Pyzza not ordered!')
        return
    else:
        logger.warning('Pyzza ordered with id %s'%order.jobID)

def start(options):
    logger.info('Let\'s put the pyzza in the oven!')
    ovenizer = OvenPyzza(options.host, options.port, options.jobID)
    if not ovenizer.putInTheOven():
        logger.warning('The oven is cold! Could not cook %s'%options.jobID)
        return
    else:
        logger.warning('Pyzza with id %s is in the oven!'%options.jobID)

def status(options):
    logger.info('Let\'s check if the pyzza is ready!')
    checker = CheckPyzza(options.host, options.port, options.jobID)
    if not checker.checkTheOven():
        logger.warning('Could not find the pyzza! %s'%options.jobID)
        return
    else:
        if checker.isReady():
            logger.warning('The Pyzza with id %s is ready!'%options.jobID)
        elif checker.isCooking():
            logger.warning('The Pyzza with id %s is still in the oven!'%options.jobID)
            logger.warning('%d slices cooked!'%(int(checker.getLastSlice()[1])))
        elif checker.isWaiting():
            logger.warning('The oven is still cold! Waiting to cook %s'%options.jobID)
        elif checker.isBurned():
            logger.warning('The Pyzza with id %s is burned!'%options.jobID)
            logger.warning('Problematic slices:')
            for err in checker.inspectErrors():
                logger.warning('Slice %d, Status %s, Ingredients %s, Return code %d'%(int(err[1]),err[0],err[2],int(err[3])))

def results(options):
    logger.info('Let me eat my pyzza!')
    eater = EatPyzza(options.host, options.port, options.jobID)
    if not eater.eatThePyzza():
        logger.error('Could not eat the pyzza! %s'%options.jobID)
        return
    else:
        for pyzzaslice in eater.getSlices():
            logger.warning('Eating slice %d'%pyzzaslice)
            for program in eater.eatSlice(pyzzaslice):
                logger.warning('Results for program %s'%program.name)
                logger.warning('Machine %s'%program.getHost())
                logger.warning('Exit status %d'%program.getExit())
                for line in program.getStdOut().splitlines():
                    logger.warning('\033[1;32m[%s]\033[0m'%line)
                for line in program.getStdErr().splitlines():
                    logger.warning('\033[1;31m[%s]\033[0m'%line)

def clean(options):
    pass

################################################################################
# Read options

def getOptions():
    # create the top-level parser
    description = "RPlauncher.py %s RunnerPyzza main script"%__version__
    parser = argparse.ArgumentParser(description = description)
    parser.add_argument('-d', '--host', action='store',
                        default='localhost',
                        help='Main server hostname')
    parser.add_argument('-p', '--port', action='store',
                        default=4123,
                        help='Main server port')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Suppress verbosity')
    parser.add_argument('-g', '--debug', action='store_true',
                        help='Add debug messages')
    subparsers = parser.add_subparsers()

    parser_init = subparsers.add_parser('init', help='Order a pyzza')
    parser_init.add_argument('-i', '--scriptChain', action="store",
                            required = True,
                            help='ScriptChain file')
    parser_init.add_argument('-m', '--machines', action="store",
                            required = True,
                            help='Machines file')
    parser_init.set_defaults(func=init)

    parser_start = subparsers.add_parser('start', help='Put the pyzza in the oven')
    parser_start.add_argument('-j', '--jobID', action="store", dest='jobID',
                            required = True,
                            help='Job ID')
    parser_start.set_defaults(func=start)
    
    parser_status = subparsers.add_parser('status', help='Check the pyzza')
    parser_status.add_argument('-j', '--jobID', action="store", dest='jobID',
                            required = True,
                            help='Job ID')
    parser_status.set_defaults(func=status)
    
    parser_results = subparsers.add_parser('results', help='Eat the pyzza')
    parser_results.add_argument('-j', '--jobID', action="store", dest='jobID',
                            required = True,
                            help='Job ID')
    parser_results.set_defaults(func=results)
    
    parser_clean = subparsers.add_parser('clean', help='Clean the table')
    parser_clean.add_argument('-j', '--jobID', action="store", dest='jobID',
                            required = True,
                            help='Job ID')
    parser_clean.set_defaults(func=clean)
    
    return parser.parse_args()

################################################################################

options = getOptions()

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
        logging.info("Bye Bye!")
    if exit:
        sys.exit()

################################################################################
# Main

def main():
    logger.info('Starting...')
    
    options.func(options)

if __name__ == '__main__':
    main()







