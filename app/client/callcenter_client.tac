from twisted.application import service, internet

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import client

top_service = service.MultiService()

shell_service = client.ShellService()
shell_service.setServiceParent(top_service)

application = service.Application('TwistedShell')

top_service.setServiceParent(application)
