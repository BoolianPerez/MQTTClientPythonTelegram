# MQTTClientPythonTelegram
## Requirements
Requires [Mosquitto](http://mosquitto.org/) to be installed.

On Linux with the **apt-get** package manager:

    sudo apt-get install mosquitto
    sudo apt-get install mosquitto-clients

**Note**: ``mosquitto-clients`` is to get the **mosquitto_pub** to make it simple to try stuff from the command line. You could leave it out and only use the supplied ``publisher.py``.

Also install [virtualenv](https://pypi.python.org/pypi/vpipx install virtualenvirtualenv) if you want to use it (recommended):

    sudo apt-get install python-virtualenv




## CONFIG MOSQUITTO 

sudo nano /etc/mosquitto/mosquitto.conf

listener 1883 0.0.0.0
pid_file /run/mosquitto/mosquitto.pid
allow_anonymous true
persistence true
persistence_location /var/lib/mosquitto/
 
log_dest file /var/log/mosquitto/mosquitto.log
 
include_dir /etc/mosquitto/conf.d




sudo systemctl restart mosquitto
## Setup
The use of virtualenv is optional but recommended for playing around with this example code.

Simply clone this repo, setup virtualenv and use pip to install requirements.

virtualenv .
source bin/activate
pip install -r requirements.txt
pip install python-telegram-bot

##Execute the server
./server.py

input the data and control it in Telegram
