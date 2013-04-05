#!/usr/bin/env python
"""hqs.py - runs the Hole Quality Scanner (HQS) user interface

Chris R. Coughlin (TRI/Austin, Inc.)
"""

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from gocator_ui import app

http_server = HTTPServer(WSGIContainer(app))
http_server.listen(5000)
IOLoop.instance().start()