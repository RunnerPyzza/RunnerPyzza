#!/usr/bin/env python
"""
XXXXXXXXXXXXX

Description
"""

__author__ = "NAME"
__copyright__ = "Copyright 20XX, PROJECT"
__credits__ = ["NAME1", "NAME2", "NAME3",
                    "NAME4"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "NAME"
__email__ = ""
__status__ = "Development"

################################################################################
# Imports

import sys
import logging
from optparse import OptionParser, OptionGroup

################################################################################
# Read options

def getOptions():
    usage = "usage: python XXXXXXXXXXXXX.py [options]"
    version="XXXXXXXXXXXXX "+str(__version__)
    description=("XXXXXXXXXXXXX")
    parser = OptionParser(usage,version=version,description=description)

    group1 = OptionGroup(parser, "")
    group1.add_option('-d', '--database', action="store", dest='db',
        default='PanGenome',
        help='Database name [PanGenome]')
    group1.add_option('-w', '--working-dir', action="store", dest='wdir',
        default='./',
        help='Working directory [./]')
    parser.add_option_group(group1)

    group2 = OptionGroup(parser, "Logging and debug")
    group2.add_option('-Q', '--quiet', action="store_true", dest='quiet',
        default=False,
        help='Quiet?')
    group2.add_option('-G', '--debug', action="store_true", dest='debug',
        default=False,
        help='Debug?')
    parser.add_option_group(group2)

    return parser.parse_args()

(options, args) = getOptions()

################################################################################
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
fh = logging.FileHandler('XXXXXXXXXXXXX.log')
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

def foo():
    '''
    Foo computes something
    Input: eggs
    Output: spam
    Exceptions: when spam > eggs
    '''
    pass

################################################################################
# Main

def XXXXXXXXXXXXX(options):
    '''
    Blah blah blah
    '''
    pass

def main():
    # Check the arguments
    if options.YYYY == '':
        logger.error('Missing mandatory parameters!')
        logger.error('Stopping XXXXXXXXXXXXX')
        sys.exit()
        
    if not options.debug:
        try:
            XXXXXXXXXXXXX(options)
        except Exception, e:
            logger.critical('ERROR: '+str(e))
    else:XXXXXXXXXXXXX(options)
    logger.info(' Stopping XXXXXXXXXXXXX')

if __name__ == '__main__':
    main()
