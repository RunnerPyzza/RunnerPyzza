from distutils.core import setup
from distutils.command.build_py import build_py
import os
import shutil
import stat
__version__ ='0.1.2'
### Change also __init__.py 



class runner_build_py(build_py):
    def runner_install(self):
        print "RunnerPyzza basic configuration ..."
        try:
            os.mkdir("/etc/runnerpyzza/")
            os.system("chmod 777 /etc/runnerpyzza/")
            #os.chmod("/etc/runnerpyzza/", stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
        except:
            pass
        try:
            os.mkdir("/etc/runnerpyzza/log")
            os.system("chmod 777 /etc/runnerpyzza/log")
            #os.chmod("/etc/runnerpyzza/log", stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
        except:
            pass
        shutil.copy2("RPdaemon.conf", "/etc/runnerpyzza/RPdaemon.conf")
        os.system("chmod 777 /etc/runnerpyzza/RPdaemon.conf")
        #os.chmod("/etc/runnerpyzza/RPdaemon.conf", stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
        print "RunnerPyzza basic configuration ... Done!"

    def run(self):
        self.runner_install()
        build_py.run(self) #run superclass method

setup(
    name = 'RunnerPyzza',
    version = __version__,
    author = 'Marco Galardina - Emilio Potenza',
    author_email = 'marco.galardini@gmail.com - emilio.potenza@gmail.com',
    packages = ['RunnerPyzza','RunnerPyzza.ClientCommon', 'RunnerPyzza.Common', 'RunnerPyzza.LauncherManager', 'RunnerPyzza.ServerCommon'], 
    scripts = ['RPdaemon','RPlauncher'],  
    #url = 'http://RunnerPyzza', 
    license = 'LICENSE.txt',
    description = 'Baciammo le mane',
    long_description = open('README.txt').read(),
    install_requires = ["paramiko >= 1.7.7.2", "argparse >= 1.1"],
    cmdclass = {"build_py" : runner_build_py}
)



