Syslog Collector
================
Syslog server which parses and handles incoming syslog messages.
Notably this server is able to parse non-compliant syslog messages as well (e.g the ones sent by busybox on embedded devices).

The idea is that the parsed messages are stored in database which a client (developed later) will be able to connect to in order to display the logs on a web-page.
