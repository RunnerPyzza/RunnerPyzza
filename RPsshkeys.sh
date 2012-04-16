#!/bin/bash
if [ "$#" -lt 2 ]; then
    echo 'sh RPsshkeys USERNAME HOSTNAME'
    exit 65
fi
USER=$1
HOST=$2
if [ -f ~/.ssh/id_dsa ]; then
    echo "ssh DSA key already present"
else
    ssh-keygen -t dsa
fi
ssh-copy-id $USER@$HOST
