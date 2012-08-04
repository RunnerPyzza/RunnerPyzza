from distutils.core import setup


__version__ ='0.1'
### Change also __init__.py in findtools dir
### Change also conf.py 

setup(
    name = 'RunnerPyzza',
    version = __version__,
    author = 'Marco Galardina - Emilio Potenza',
    author_email = 'marco.galardini@gmail.com - emilio.potenza@gmail.com',
    packages = ['findtools', "findtools.test"],
    scripts = ['bin/findASpsb','bin/findCLEAN', "bin/statBAM", "bin/statASpsb"],  
    #url = 'http://pypi.python.org/pypi/findTools/', 
    license = 'LICENSE.txt',
    description = 'Useful ngs-related stuff',
    long_description = open('README.txt').read(),
    install_requires = ["pysam >= 0.6", "psutil >= 0.4.1"]
)



