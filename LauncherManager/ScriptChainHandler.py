#!/usr/bin/env python
"""
ScriptChainHandler

LauncherManager package

High-level methods to handle a script chain, calling external parsers
"""

__author__ = "Marco Galardini"
__copyright__ = "Copyright 2011, RunnerPyzza"
__credits__ = ["Emilio Potenza"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Marco Galardini"
__email__ = "marco.galardini@unifi.it"
__status__ = "Development"

################################################################################
# Imports

import logging

################################################################################
# Log setup

# create logger
# Name shown
logger = logging.getLogger('ScriptChainHandler')

################################################################################
# Classes

class Handler(object):
    '''
    Class Parser
    Wrapper for the Launcher XML parser
    '''
    def __init__(self,infile):
        self._infile = infile
        self._scriptChain = None
        self.programs = []
    def parse(self):
        '''
        Calls the XML parser and stores the parsed object for further analysis
        '''
        logging.debug(('Parsing ScriptChain file %s'%self._infile))
        
        # Parse
        from ClientCommon import ScriptChainXML as SCXml
        doc = SCXml.parsexml_(self._infile)
        rootNode = doc.getroot()
        rootTag, rootClass = SCXml.get_root_tag(rootNode)
        if rootClass is None:
            rootTag = 'ScriptChainHandler'
            rootClass = SCXml.scriptChain
        rootObj = rootClass.factory()
        rootObj.build(rootNode)

        # Store the object
        self._scriptChain = rootObj
    def _assembleOption(self,option):
        '''
        Assembles the options elements
        '''
        # Handle NoneType
        if not option.getDelimiter():
            delimit = ''
        else:
            delimit = option.getDelimiter()
        if not option.getSeparator():
            sep = ''
        else:
            sep = option.getSeparator()
        if not option.getAlias():
            alias = ''
        else:
            alias = option.getAlias()
        return ' '+sep.join([
                           alias,
                           delimit+option.getValue()+delimit    
                           ])
    def _assembleCpu(self,cpu):
        '''
        Assembles the cpus elements
        '''
        return cpu.getCmdcpu()+str(cpu.getNumcpu())
    def createCommands(self):
        '''
        Iterates over the programs and creates a series of commands object
        '''
        from Common import Program as PRG
        for program in self._scriptChain.getProgram():
            name = program.getMain().getName()
            cmd = program.getMain().getBasecommand()
            # Add options - if any
            if program.getOption():
                for option in program.getOption():
                    cmd += self._assembleOption(option)
            # Add cpu usage informations - if any
            if program.getCpu():
                ncpu = program.getCpu().getNumcpu()
                if program.getCpu().getKind() == 'prefix':
                    cmd = self._assembleCpu(program.getCpu()) + ' ' + cmd
                else:
                    cmd += ' '+self._assembleCpu(program.getCpu())
            # Create the final object and put it into the list
            progObj = PRG.Program(name,cmd)
            # Put the order
            progObj.setOrder(program.getMain().getOrder())
            if program.getCpu():
                progObj.setCpu(ncpu)
            self.programs.append(progObj)
            
            logging.debug(
                'Created program %s, using %d CPUs'%(progObj.name,
                                                     progObj.getCpu()))
        
        # Order the programs looking at their order attribute
        self.programs = sorted(self.programs, key=lambda p: p.getOrder())
        
        logging.debug('Parsed %d programs'%len(self.programs))
    def getSimpleSH(self):
        '''
        Returns a simple string that can be used as a shell script
        '''
        if self.programs == []:
            self.createCommands()
        prg_list = []
        for prg in self.programs:
            prg_list.append(str(prg))
        return '\n'.join(prg_list)
    
################################################################################
# Methods

################################################################################
# Main

if __name__ == '__main__':
    pass
