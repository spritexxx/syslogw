import argparse
import logging
import Queue

from threading import Thread

from twisted.internet import reactor

import viewer
import servers
import parsers
import mongodb

__author__ = 'Simon Esprit'

# Defaults
DEFAULT_PORT = 5140
DEFAULT_VIEWER_PORT = 8181
DEFAULT_MAX_THREADS = 2
DEFAULT_COLLECTION = "messages"


def read_arguments():
    """
    Read commandline arguments that alter behavior of this program.
    :return:
    """
    parser = argparse.ArgumentParser(description='Syslog Collector')

    parser.add_argument('--transport', type=str, choices=['udp', 'tcp'], help='Transport protocol used.')
    parser.add_argument('--log', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Specify desired log level.")
    parser.add_argument('--parser', type=str, choices=available_parsers(), help="Only try to parse the syslog messages with this parser.")
    parser.add_argument('--database', type=str, choices=['y', 'n'], help="Store logs in a database or not.")
    parser.add_argument('--serverip', type=str, help="specify server ip address (e.g IP of the server hosting this app)")

    # ports below 1024 need sudo privileges so we don't allow them for the web viewer
    parser.add_argument('--viewer_port', type=int, help="specify port to use for the viewer")
    parser.add_argument('--server_port', type=int, help="specify port to use for the server")

    return parser.parse_args()


def available_parsers():
    list = []
    for parser in parsers.Parser.__subclasses__():
        for subclass in parser.__subclasses__():
            if subclass.name():
                list.append(subclass.name())

        if parser.name():
            list.append(parser.name())

    return list


def get_parser_by_name(name):
    """
    Lookup a parser by its name.
    :param name: string name of the parser
    :return: parsers class if found or None if not found
    """
    for parser in parsers.Parser.__subclasses__():
        for subclass in parser.__subclasses__():
            if subclass.name() == name:
                return subclass

        if parser.name() == name:
            return parser

    return None


def handle_new_messages(work_queue, factory, database=None, parser=None):
    """
    Worker thread that handles incoming syslog messages.
    :param work_queue: Queue containing raw received messages.
    :param database: Connection to the database where messages can be stored.
    :param factory: Connection to web socket clients.
    :param parser: Parser class to be used for parsing the messages.
    :return: Nothing at all.
    """
    while True:
        raw_data = work_queue.get()

        message = raw_data.parse_message(parser)

        if message is None:
            # TODO notify client about unparsed messages?
            work_queue.task_done()
            continue

        # add extra fields to message
        json_message = message.as_dict()
        json_message['rx_timestamp'] = raw_data.timestamp
        json_message['origin_ip'] = raw_data.origin_ip

        # also inform all clients about new data
        # this call returns immediately thanks to twisted
        reactor.callFromThread(factory.updateClients, json_message)

        # store in database
        if database:
            # create copy as database tends to modify the dict
            database.store_message_data(dict(json_message))
        else:
            # print to debug logs
            logging.debug(raw_data.message)

        work_queue.task_done()


def main():
    args = read_arguments()

    if args.log is not None:
        # set the root logger level
        numeric_level = getattr(logging, args.log.upper())
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s.' % args.log.upper())

        logging.basicConfig(level=numeric_level)

    if not args.database:
        database = None
    else:
        if args.database == "y":
            # mongo db connection that will be shared between the threads
            database = mongodb.MongoDBConnection(DEFAULT_COLLECTION)
            if not database.connect():
                logging.warning("Could not connect to mongod, not saving logs in DB!")
                database = None
            else:
                logging.info("Connected to database.")
        else:
            database = None

    if not database:
        logging.warn("Not storing logs in database...")

    if args.parser:
        parser = get_parser_by_name(args.parser)
        if not parser:
            print("Error: did not find specified parser: %s" % args.parser)
            return 1
        else:
            logging.info("Using parser class %s" % parser.__name__)
    else:
        parser = None

    # create factory for viewer websockets
    factory = servers.SyslogViewerFactory(u"ws://127.0.0.1:9494")
    reactor.listenTCP(9494, factory)

    # create Queue for handling incoming messages
    work_queue = Queue.Queue()

    # threads that will parse & handle received messages
    for i in range(DEFAULT_MAX_THREADS):
        worker = Thread(target=handle_new_messages, args=(work_queue, factory, database, parser))
        worker.setDaemon(True)
        worker.start()

    server_port = args.server_port if args.server_port else DEFAULT_PORT
    # default transport is udp
    if not args.transport:
        reactor.listenUDP(server_port, servers.SyslogUdp(work_queue))
    else:
        if args.transport == "udp":
            logging.info("Starting UPD server.")
            reactor.listenUDP(server_port, servers.SyslogUdp(work_queue))
        elif args.transport == "tcp":
            logging.info("Starting TCP server.")
            Exception("TCP not supported yet!")

    # create a viewer
    viewer_port = args.viewer_port if args.viewer_port else DEFAULT_VIEWER_PORT
    viewer.create_viewer(reactor, viewer_port, args.serverip)

    reactor.run()
    print("Syslog Collector Server stopped.")

if __name__ == "__main__":
    main()