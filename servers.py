import parsers
import logging
import json

from twisted.internet import protocol
from autobahn.twisted import WebSocketServerProtocol, WebSocketServerFactory
from twisted.internet import reactor

__author__ = 'Simon Esprit'


class SyslogUdp(protocol.DatagramProtocol):
    """
    Protocol for receiving syslog messages over UDP.
    """
    def __init__(self, work_queue):
        self.work_queue = work_queue

    """
    Simple protocol which receives syslog data over UDP.
    """
    def datagramReceived(self, data, addr):
        self.work_queue.put(parsers.RawSyslogData(data, addr[0]))


class SyslogViewerProtocol(WebSocketServerProtocol):
    """
    Websocket protocol that is used to push new incoming syslog messages
    to the viewer client.
    """
    def onConnect(self, request):
        logging.debug("Client connecting {0}".format(request.peer))

    def onOpen(self):
        # register yourself in so that you can get updates
        self.factory.clients.append(self)

    def onMessage(self, payload, isBinary):
        if isBinary:
            logging.debug("RX (binary)")
        else:
            logging.debug("RX - {0}".format(payload.decode('utf8')))

    def onClose(self, wasClean, code, reason):
        # it can be that we are somehow not in anymore
        if self in self.factory.clients:
            self.factory.clients.remove(self)
        logging.debug("Client connection closed, reason: {0}".format(reason))

    def newMessage(self, message):
        try:
            payload = json.dumps(message, ensure_ascii=False).encode('utf8')
            # simply push message to client
            self.sendMessage(payload)
        except Exception as e:
            logging.warn("exception occurred: " + str(e))


class SyslogViewerFactory(WebSocketServerFactory):
    """
    Factory that keeps track of all connected websockets
    and can be triggered from worker threads to push new messages
    to the clients.
    """
    protocol = SyslogViewerProtocol
    clients = []

    # called by worker threads in case they have new data for the clients
    def updateClients(self, message):
        for proto in self.clients:
            # call in thread so that a client cannot block us!
            reactor.callInThread(proto.newMessage, message)
