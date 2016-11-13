import argparse
import logging

from twisted.internet import reactor

import servers

__author__ = 'Simon Esprit'

# Defaults
DEFAULT_PORT = 5140


def read_arguments():
    """
    Read commandline arguments that alter behavior of this program.
    :return:
    """
    parser = argparse.ArgumentParser(description='Syslog Collector')
    parser.add_argument('format', type=str, choices=['busybox', 'rcf'], help="Format of the received syslog messages.")
    parser.add_argument('transport', type=str, choices=['udp', 'tcp'], help='Transport protocol used.')
    parser.add_argument('storage', type=str, choices=['file', 'database'], help='How to store incoming data.')

    # search options
    parser.add_argument('--log', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Specify desired log level.")

    return parser.parse_args()


def main():

    args = read_arguments()

    if args.log is not None:
        # set the root logger level
        numeric_level = getattr(logging, args.log.upper())
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s.' % args.log.upper())

        logging.basicConfig(level=numeric_level)

    if args.transport == "udp":
        logging.info("Starting UPD server.")
        reactor.listenUDP(DEFAULT_PORT, servers.SyslogUdp())
    elif args.transport == "tcp":
        logging.info("Starting TCP server.")
        Exception("TCP not supported yet!")

    print("Syslog Collector Server listening on port %d (%s)" % (DEFAULT_PORT, args.transport.upper()))

    reactor.run()
    print("Syslog Collector Server stopped.")

if __name__ == "__main__":
    main()