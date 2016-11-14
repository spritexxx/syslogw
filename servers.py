import logging
import json

import parsers

from twisted.internet import reactor, protocol

__author__ = 'Simon Esprit'


class SyslogUdp(protocol.DatagramProtocol):
    def __init__(self, work_queue):
        self.work_queue = work_queue

    """
    Simple protocol which receives syslog data over UDP.
    """
    def datagramReceived(self, data, addr):
        self.work_queue.put(parsers.RawSyslogData(data, addr[0]))
