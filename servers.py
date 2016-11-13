import logging
import json

import parsers

from twisted.internet import reactor, protocol

__author__ = 'Simon Esprit'


class SyslogUdp(protocol.DatagramProtocol):
    """
    Simple protocol which receives syslog data over UDP.
    """
    def datagramReceived(self, data, addr):
        raw_data = parsers.RawSyslogData(data, addr[0])

        # try and parse the message
        message = parsers.RFC5424Parser.parse_message(raw_data.message)
        if message is None:
            message = parsers.BusyboxParser.parse_message(raw_data.message)

        if message is not None:
            logging.debug(json.dumps(message.as_dict()))
