#!/usr/bin/env bash

hosts=( alho1 alho2 )

for host in "${hosts[@]}"
do
    ssh $host "
        sudo pkill -c python || true
        cd ~/CamTransport
        git pull
        nohup python main_client.py > /dev/null 2> /dev/null < /dev/null &"
done

