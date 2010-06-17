#!/usr/bin/python

""" Debian Smart Upload Server runtime

@copyright: 2010  Petr Jasek <jasekpetr@gmail.com>
@license: GNU General Public License version 2 or later
"""

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

################################################################################

import sys
import getopt
import signal
import hashlib
import BaseHTTPServer

from dsus_handler import DSUSHandler

config = {
	"port": 8000,
	"dest": "./",
	}

STATE_INIT = 0
STATE_ACTIVE = 1
STATE_SHUTDOWN = 2

server_state = STATE_INIT

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
	server_address = ("", config["port"])
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
			config["port"] = int(arg)

	run(handler_class=DSUSHandler)

if __name__ == "__main__":
	main(sys.argv[1:])

