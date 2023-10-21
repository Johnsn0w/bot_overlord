#!/bin/bash    

# retrieve first argument passed to script and store as variable
# environment=$1

cd /mr_robot

apt-get update && apt-get install -y git
# the repo already exists as a bind mount to a host dir (provided you haven't forgot to set it on on the host)
pip3 install -r requirements.txt

RUN chmod +x ./bot_main.py
