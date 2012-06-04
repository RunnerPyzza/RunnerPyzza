#!/bin/bash
if [ $UID -ne 0 ]; then
   echo "$0 must be run as root"
   exit 1
fi
useradd -m runnerpyzza
passwd runnerpyzza
id runnerpyzza > /dev/null
if [ $? -ne 0 ]; then
   echo "Could not create the user runnerpyzza!"
   exit $?
fi
echo "User runnerpyzza successefully created"
