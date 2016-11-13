import logging

from twisted.internet import reactor, protocol

__author__ = 'Simon Esprit'


class SyslogUdp(protocol.DatagramProtocol):
    """
    Simple protocol which receives syslog data over UDP.
    """
    def datagramReceived(self, data, addr):
        logging.debug("received %r from %s" % (data, addr))
