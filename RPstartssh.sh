#!/bin/bash
SOCKET=~/.ssh/agent.socket
ENV=~/.ssh/agent.env
ssh-agent -a $SOCKET > $ENV
export SSH_AUTH_SOCK=~/.ssh/agent.socket
