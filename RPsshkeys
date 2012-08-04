#!/bin/bash
if [ "$#" -lt 2 ]; then
    echo './RPsshkeys USERNAME HOSTNAME'
    exit 65
fi
USER=$1
HOST=$2
if [ -f ~/.ssh/id_rsa ]; then
    echo "ssh RSA key already present"
else
    ssh-keygen -t rsa
fi
ssh-add
ssh-copy-id $USER@$HOST
