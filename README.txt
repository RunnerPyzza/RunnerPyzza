RunnerPyzza
===========

An easy to use queue system for laboratory networks
---------------------------------------------------

The readme is still under construction, hang tight!

Quick how-to
------------

- RunnerPyzza server installation on the main machine
python setup.py sdist
sudo pip install dist/RunnerPyzza-X.X.X.tar.gz
sudo RPadduser
sudo RPaddservice
- Cloud setup (edit /etc/runnerpyzza/RPdaemon.conf and check that all the machines are connected through NFS)
sudo service runnerpyzza restart
- Recipe creation (no tool available for now, but you can start from the example file)
- Order your beloved pyzza!
RPlauncher auto YourRecipe.xml
- RPlauncher offers also the opportunity to launch single commands
RPlauncher init YourRecipe.xml
RPlauncher start Margherita_XXXX
RPlauncher status Margherita_XXXX
RPlauncher results Margherita_XXXX
RPlauncher clean Margherita_XXXX
- If something goes wrong you can check the main server log (/etc/runnerpyzza/log/RPdaemon.log
