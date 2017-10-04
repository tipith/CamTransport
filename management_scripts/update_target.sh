#!/usr/bin/env bash

ssh $1 "
    sudo pkill -c python || true
    cd ~/CamTransport
    git pull
    nohup python main_client.py > /dev/null 2> /dev/null < /dev/null &"

