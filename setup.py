from distutils.core import setup


__version__ ='0.1'
### Change also __init__.py in findtools dir
### Change also conf.py 

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
    install_requires = ["paramiko >= 1.7.7.2", "argparse >= 1.1"]
)



