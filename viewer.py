from flask import Flask

from twisted.web import server, static
from twisted.web.wsgi import WSGIResource


__author__ = 'Simon Esprit'

client_app = Flask(__name__)


@client_app.route('/')
def index():
    # TODO put a real implementation using templates etc...
    return '<h1>Syslog Viewer</h1>'


@client_app.route('/websocket.html')
def websocket_test():
    """
    This is really just an example of how to server a static page
    that can also be used for testing the websocket communication.
    """
    return client_app.send_static_file('websocket.html')


def create_viewer(reactor, port):
    wsgi_resource = WSGIResource(reactor, reactor.getThreadPool(), client_app)
    site = server.Site(wsgi_resource)
    reactor.listenTCP(port, site, interface="0.0.0.0")

