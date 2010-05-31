#!/usr/bin/env python
# dsus.py

import sys
import getopt
import signal
import BaseHTTPServer

SERVER_ADDRESS = 8000
SERVER_VERSION = "DSUS/0.1"

options = {
	"port": SERVER_ADDRESS,
	"dest": "./",
	}

STATE_INIT = 0
STATE_ACTIVE = 1
STATE_SHUTDOWN = 2

server_state = STATE_INIT

class DSUSHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	"""
	Handler for Debian Smart Upload Server Protocol.
	"""

	server_version = SERVER_VERSION

	def do_GET(self):
		"""
		Command handle.
		"""
		self.send_response(200, "OK")
		self.end_headers()
	
	def du_PUT(self):
		"""
		File uploading handle.
		"""
		self.send_response(200, "OK")

def usage():
	"""
	Print usage message.
	"""

	print "usage: dsus.py [-p|--port=SERVER_PORT] [-h|--help]"

def load_config():
	"""
	Loads config.
	"""

	print "Config load call."

def handle_signal(signum, frame):
	"""
	Change server state with signals.
	"""

	if signum == signal.SIGUSR1:
		global server_state
		server_state = STATE_SHUTDOWN
		print "Server shutting down."

	elif signum == signal.SIGHUP:
		load_config()
		print "Config reloaded."

def run(server_class=BaseHTTPServer.HTTPServer,
		handler_class=BaseHTTPServer.BaseHTTPRequestHandler):
	"""
	Server routine.
	"""

	server_address = ("", options["port"])
	httpd = server_class(server_address, handler_class)

	# Set signals handles.
	global server_state
	server_state = STATE_ACTIVE
	signal.signal(signal.SIGUSR1, handle_signal)
	signal.signal(signal.SIGHUP, handle_signal)

	while server_state == STATE_ACTIVE:
		httpd.handle_request()

def main(argv):
	"""
	Handles arguments and runs server.
	"""

	try:
		opts, args = getopt.getopt(argv, "hp:", ["help", "port="])
	except getopt.GetoptError:
		usage()
		sys.exit(2)

	# parse options
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()
			sys.exit()
		elif opt in ("-p", "--port"):
			options["port"] = arg

	run(handler_class=DSUSHandler)

if __name__ == "__main__":
	main(sys.argv[1:])

