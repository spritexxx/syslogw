Syslogw (syslog web)
=====================
This is a syslog collector (server) which parses and stores incoming syslog messages in a database and makes them available
through a web application.

Notably this server is able to parse non-compliant syslog messages as well (e.g the ones sent by busybox on embedded devices).

Requirements
-------------
* python 2.7 
* pip install -r requirements.txt
* optionally: mongodb (tested on v3.2.10) if you specify --database=y

Note:
I had SSL related issues on my macbook which made pip unable to install twisted.
To fix this I had to do the following:
* pip install certifi

From then on everything was smooth sailing!

How to use
-----------
1. Optional: Make sure mongodb is installed and running.
2. Start the server:
    python syslogw.py
        optionally specify --log=DEBUG if you want to see incoming messages on the console

Note:
Currently the server listens on port 5140 (UDP) only and TCP connections are not yet supported.

To test
-------
$  logger --server [your_ip] --port 5140 my awesome message

If you have debug enabled (--log=DEBUG) you should see this on the console.
However, you can always view them using mongo:
$ mongo
>> use syslog
>> db.messages.show()

If your logger does not allow you to specify a server and port you can always 
update the /etc/syslog.conf file so that it logs certain messages to a server.

This line forwards all messages to a server for example:
*.* 			@127.0.0.1:5140

Web app
--------
To view the web app, fire up a browser and go to:
localhost:8181


Syslog-ng
----------
In case you want to forward logs to the server from syslog-ng running on a client,
you can copy the example syslog-ng configuration file found in conf/syslog-ng to
/etc/syslog-ng/conf.d/syslogw.conf

Note that customization of the ip address and port might be necessary!

Extended options
----------------
This will list all available options:
	python syslogw.py --help
