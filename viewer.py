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
    return render_template('viewer.html')


@app.route('/websocket.html')
def websocket_test():
    """
    This is really just an example of how to server a static page
    that can also be used for testing the websocket communication.
    """
    return app.send_static_file('websocket.html')


def create_viewer(reactor, port):
    # add extension to the app
    bootstrap = Bootstrap(app)

    wsgi_resource = WSGIResource(reactor, reactor.getThreadPool(), app)
    site = server.Site(wsgi_resource)
    reactor.listenTCP(port, site, interface="0.0.0.0")

