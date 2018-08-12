#!/usr/bin/env bash

source targets.sh

for host in "${hosts[@]}"
do
    ssh $host "
        sudo pkill -c python || true
        cd ~/CamTransport
        git pull
        nohup python main_client.py > /dev/null 2> /dev/null < /dev/null &"
done

