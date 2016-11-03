#!/usr/bin/env bash

hosts=( alho1 alho2 )

for host in "${hosts[@]}"
do
    ssh $host "
        sudo apt-get -y update
        sudo apt-get -y dist-upgrade"
done

