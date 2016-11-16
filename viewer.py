import logging
import json

from autobahn.twisted import WebSocketServerProtocol, WebSocketServerFactory
from twisted.internet import reactor

__author__ = 'Simon Esprit'


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
        payload = json.dumps(message, ensure_ascii=False).encode('utf8')
        # simply push message to client
        self.sendMessage(payload)


class SyslogViewerFactory(WebSocketServerFactory):
    protocol = SyslogViewerProtocol
    clients = []

    # called by worker threads in case they have new data for the clients
    def updateClients(self, message):
        for proto in self.clients:
            # call in thread so that a client cannot block us!
            reactor.callInThread(proto.newMessage, message)
