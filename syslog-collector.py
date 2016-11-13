import argparse
import logging
import Queue
import json
from threading import Thread

from twisted.internet import reactor

import servers
import parsers

__author__ = 'Simon Esprit'

# Defaults
DEFAULT_PORT = 5140
DEFAULT_MAX_THREADS = 2


def read_arguments():
    """
    Read commandline arguments that alter behavior of this program.
    :return:
    """
    parser = argparse.ArgumentParser(description='Syslog Collector')
    parser.add_argument('transport', type=str, choices=['udp', 'tcp'], help='Transport protocol used.')
    parser.add_argument('storage', type=str, choices=['file', 'database'], help='How to store incoming data.')

    parser.add_argument('--log', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Specify desired log level.")
    parser.add_argument('--format', type=str, choices=['busybox', 'rfc'], help="Only try to parse the syslog messages with this format.")

    return parser.parse_args()


def handle_new_messages(work_queue):
    while True:
        raw_data = work_queue.get()

        # try and parse the message
        message = parsers.RFC5424Parser.parse_message(raw_data.message)
        if message is None:
            message = parsers.BusyboxParser.parse_message(raw_data.message)

        if message is not None:
            logging.debug(json.dumps(message.as_dict()))

        work_queue.task_done()


def main():

    args = read_arguments()

    if args.log is not None:
        # set the root logger level
        numeric_level = getattr(logging, args.log.upper())
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s.' % args.log.upper())

        logging.basicConfig(level=numeric_level)

    # Create Queue for handling incoming messages
    work_queue = Queue.Queue()

    # Threads that will parse & handle received messages
    for i in range(DEFAULT_MAX_THREADS):
        worker = Thread(target=handle_new_messages, args=(work_queue,))
        worker.setDaemon(True)
        worker.start()

    if args.transport == "udp":
        logging.info("Starting UPD server.")
        reactor.listenUDP(DEFAULT_PORT, servers.SyslogUdp(work_queue))
    elif args.transport == "tcp":
        logging.info("Starting TCP server.")
        Exception("TCP not supported yet!")

    print("Syslog Collector Server listening on port %d (%s)" % (DEFAULT_PORT, args.transport.upper()))

    reactor.run()
    print("Syslog Collector Server stopped.")

if __name__ == "__main__":
    main()