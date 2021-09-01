from twisted.application import service, internet

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import manager

# Default port in case the env var was not properly set
CC_SERVER_PORT = 5678

proxy_port = int(os.environ.get('CC_SERVER_PORT', CC_SERVER_PORT))

application = service.Application('TwistedDockerized')
factory = manager.RequestFactory()
server = internet.TCPServer(proxy_port, factory)
server.setServiceParent(application)
