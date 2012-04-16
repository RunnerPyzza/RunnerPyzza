#!/bin/bash
if [ "$#" -lt 2 ]; then
    echo 'sh RPsshkeys USERNAME HOSTNAME'
    exit 65
fi
USER=$1
HOST=$2
ssh-keygen -t dsa
ssh-copy-id $USER@$HOST
