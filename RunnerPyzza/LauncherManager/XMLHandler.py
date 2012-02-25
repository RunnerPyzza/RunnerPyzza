#!/usr/bin/env python
"""
XMLHandler

LauncherManager package

High-level methods to handle the various xml related to Launcher
"""

__author__ = "Marco Galardini"
__credits__ = ["Emilio Potenza"]

import logging

################################################################################
# Log setup

# create logger
# Name shown
logger = logging.getLogger('RunnerPyzza.XMLHandler')

################################################################################
# Classes

class GenericHandler(object):
    def __init__(self,inXML):
        try:
            open(inXML)
            self._inXML = inXML
            logging.debug('XML file name passed as input')
        except:
            import StringIO
            self._inXML = StringIO.StringIO()
            self._inXML.write(inXML)
            self._inXML.seek(0)
            logging.debug('XML string passed as input')
            
    def send(self):
        pass

class ScriptChain(GenericHandler):
    '''
    Class ScriptChain
    Wrapper for the Launcher XML parser
    The XML document has to be passed upon object creation: it can either be
    a string containing directly the XML or the filename.
    '''
    def __init__(self,inXML):
        GenericHandler.__init__(self,inXML)
        self._scriptChain = None
        self.programs = []
        
    def __str__(self):
        '''
        Returns a simple string that can be used as a shell script
        '''
        if self.programs == []:
            self.createCommands()
        prg_list = []
        for prg in self.programs:
            prg_list.append(str(prg))
        return '\n'.join(prg_list)
    
    def parse(self):
        '''
        Calls the XML parser and stores the parsed object for further analysis
        '''
        logging.debug(('Parsing ScriptChain xml'))
        
        # Parse
        from RunnerPyzza.ClientCommon import ScriptChainXML as SCXml
        doc = SCXml.parsexml_(self._inXML)
        rootNode = doc.getroot()
        rootTag, rootClass = SCXml.get_root_tag(rootNode)
        if rootClass is None:
            rootTag = 'scriptChain'
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
        # Handle NoneType
        if not cpu.getDelimiter():
            delimit = ''
        else:
            delimit = cpu.getDelimiter()
        if not cpu.getSeparator():
            sep = ''
        else:
            sep = cpu.getSeparator()
        return cpu.getCmdcpu()+sep+delimit+str(cpu.getNumcpu())+delimit
    
    def createCommands(self):
        '''
        Iterates over the programs and creates a series of commands object
        '''
        if not self._scriptChain:
            self.parse()
            
        from RunnerPyzza.Common import Program as PRG
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
            # Check the failure flag
            if program.getCanFail():
                canFail = program.getCanFail()
            # Create the final object and put it into the list
            progObj = PRG.Program(name,cmd)
            # Put the order
            progObj.setOrder(program.getMain().getOrder())
            if program.getCpu():
                progObj.setCpu(ncpu)
            if program.getCanFail():
                progObj.setCanFail(canFail)
            self.programs.append(progObj)
            
            logging.info(
                'Created program %s, using %d CPUs'%(progObj.name,
                                                     progObj.getCpu()))
        
        # Order the programs looking at their order attribute
        self.programs = sorted(self.programs, key=lambda p: p.getOrder())
        
        logging.debug('Parsed %d programs'%len(self.programs))
        
    def getPrograms(self):
        if self.programs == []:
            self.createCommands()
        return self.programs

class MachinesSetup(GenericHandler):
    def __init__(self,inXML):
        GenericHandler.__init__(self,inXML)
        self._machinesSetup = None
        self.machines = []
        
    def __str__(self):
        '''
        Returns a simple string that represents the machine
        '''
        if self.machines == []:
            self.createMachines()
        mch_list = []
        for mch in self.machines:
            mch_list.append(str(mch))
        return '\n'.join(mch_list)
    
    def parse(self):
        '''
        Calls the XML parser and stores the parsed object for further analysis
        '''
        logging.debug(('Parsing MachinesSetup xml'))
        
        # Parse
        from RunnerPyzza.ClientCommon import MachinesSetupXML as MSXml
        doc = MSXml.parsexml_(self._inXML)
        rootNode = doc.getroot()
        rootTag, rootClass = MSXml.get_root_tag(rootNode)
        if rootClass is None:
            rootTag = 'machinesSetup'
            rootClass = MSXml.machinesSetup
        rootObj = rootClass.factory()
        rootObj.build(rootNode)

        # Store the object
        self._machinesSetup = rootObj
        
    def createMachines(self):
        '''
        Iterates over the machines and creates a series of machines object
        '''
        if not self._machinesSetup:
            self.parse()
        
        from RunnerPyzza.Common import Machine as MCH
        
        for machine in self._machinesSetup.getMachine():
            self.machines.append(MCH.Machine(machine.name,
                                             machine.getHostname(),
                                             machine.getUser()))
            logging.info(
                'Added "%s", with hostname %s and user %s'
                            %(machine.name,
                              machine.getHostname(),
                              machine.getUser()))
        
        logging.debug('Parsed %d machines'%len(self.machines))
        
    def getMachines(self):
        if self.machines == []:
            self.createMachines()
        return self.machines

################################################################################
# Methods

################################################################################
# Main

if __name__ == '__main__':
    pass
