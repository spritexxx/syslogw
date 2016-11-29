import socket
import logging


from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask import request

from twisted.web import server
from twisted.web.wsgi import WSGIResource


__author__ = 'Simon Esprit'

app = Flask(__name__)


@app.before_request
def log_request():
    """
    Function that can be used to log incoming requests.
    """
    app.logger.debug(request.path)


@app.route('/')
def index():
    return render_template('viewer.html', server_ip=app.config['SERVER_IP'])


@app.route('/websocket.html')
def websocket_test():
    """
    This is really just an example of how to server a static page
    that can also be used for testing the websocket communication.
    """
    return app.send_static_file('websocket.html')


def create_viewer(reactor, port, server_ip=None):
    # figure out our IP in case it is not specified
    if not server_ip:
        hostname = socket.gethostname()
        serverip = socket.gethostbyname(hostname)
        if serverip == "127.0.0.1":
            serverip = hostname + ".local"
    else:
        serverip = server_ip

    print("viewer listening on {0}:{1}".format(serverip, port))

    app.config['SERVER_IP'] = serverip

    # add extension to the app
    bootstrap = Bootstrap(app)

    wsgi_resource = WSGIResource(reactor, reactor.getThreadPool(), app)
    site = server.Site(wsgi_resource)
    reactor.listenTCP(port, site, interface="0.0.0.0")

