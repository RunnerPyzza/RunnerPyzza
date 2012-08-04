#!/bin/bash
if [ $UID -ne 0 ]; then
   echo "$0 must be run as root"
   exit 1
fi
mkdir /opt/runnerpyzza
chmod 777 -R /opt/runnerpyzza
ls /opt/runnerpyzza > /dev/null
if [ $? -ne 0 ] ; then
  echo "Could not create RunnerPyzza directory"
else
  echo "RunnerPyzza directory successefully created"
fi
