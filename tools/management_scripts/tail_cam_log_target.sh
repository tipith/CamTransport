#!/usr/bin/env bash

ssh -t $1 "tail -n 80 -f ~/CamTransport/log.txt;"

