from distutils.core import setup
from distutils.command.build_py import build_py
import os
import shutil
import stat
from RunnerPyzza import __version__ 

class runner_build_py(build_py):
    def runner_install(self):
        print "RunnerPyzza basic configuration ..."
        try:
            os.mkdir("/etc/runnerpyzza/")
        except:
            pass
        try:
            os.mkdir("/etc/runnerpyzza/log")
            os.system("chmod 777 /etc/runnerpyzza/log")
        except:
            pass
        shutil.copy2("RPdaemon.conf", "/etc/runnerpyzza/RPdaemon.conf")
        shutil.copy2("runnerpyzza", "/etc/runnerpyzza/runnerpyzza")
        try:
            os.system("chmod 755 /etc/runnerpyzza/runnerpyzza")
        except:
            pass
        print "RunnerPyzza basic configuration ... Done!"

    def run(self):
        self.runner_install()
        build_py.run(self) #run superclass method

setup(
    name = 'RunnerPyzza',
    version = __version__,
    author = 'Marco Galardini - Emilio Potenza',
    author_email = 'marco.galardini@gmail.com - emilio.potenza@gmail.com',
    packages = ['RunnerPyzza','RunnerPyzza.ClientCommon', 'RunnerPyzza.Common', 'RunnerPyzza.LauncherManager', 'RunnerPyzza.ServerCommon'], 
    scripts = ['RPdaemon','RPlauncher','RPaddservice','RPadduser','RPpreparedir','RPsshkeys'],  
    #url = 'http://RunnerPyzza', 
    license = 'LICENSE.txt',
    description = 'Baciammo le mane',
    long_description = open('README.txt').read(),
    install_requires = ["paramiko >= 1.7.7.2", "argparse >= 1.1"],
    cmdclass = {"build_py" : runner_build_py}
)



