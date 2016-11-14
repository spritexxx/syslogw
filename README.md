Syslog Collector
=================
This is a syslog collector (server) which parses and stores incoming syslog messages in a database and makes them available
through a web application.

Notably this server is able to parse non-compliant syslog messages as well (e.g the ones sent by busybox on embedded devices).

Requirements
-------------
* python 2.7 
* pip install -r requirements.txt
* mongodb (tested on v3.2.10)

How to use
-----------
1. Make sure mongodb is installed and running.
2. Start the server:
    python syslog-collector.py udp
        optionally specify --log=DEBUG if you want to see incoming messages on the console

Note:
Currently the server listens on port 5140 (UDP) only and TCP connections are not yet supported.

To test
-------
$  logger --server 10.0.0.1 --port 5140 my awesome message

If you have debug enabled (--log=DEBUG) you should see this on the console.
However, you can always view them using mongo:
$ mongo
>> use syslog
>> db.messages.show()

Web app
--------
The web app to view the logged messages is a work in progress.
For now you can find them in syslog database (mongodb) under the messages collections.
