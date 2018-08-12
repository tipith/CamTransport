#!/usr/bin/env bash

source targets.sh

for host in "${hosts[@]}"
do
    ssh $host "
        #pip list --outdated
        #pip freeze --local | grep -v '^\-e' | cut -d = -f 1  | sudo xargs -n1 pip install -U
        sudo apt-get update && sudo apt-get -y upgrade
        sudo pkill -c python || true
        cd ~/CamTransport
        nohup python main_client.py > /dev/null 2> /dev/null < /dev/null &"
done

