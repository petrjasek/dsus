#!/usr/bin/env python
# dsus.py

import sys
import getopt
import signal
import os.path
from glob import iglob
import time
import re
import tempfile
import hashlib
import shutil
import BaseHTTPServer
from urlparse import urlparse

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

CHANGES = '.changes'
COMMANDS = '.commands'
SIGNED = (CHANGES, COMMANDS)

WINDOW = 3600 * 24 # secs we wait for files after .changes recieved

class DSUSHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	"""
	Handler for Debian Smart Upload Server Protocol.
	"""

	server_version = SERVER_VERSION

	dirname = None
	filename = None
	md5 = None
	length = 0

	def do_PUT(self):
		"""
		File uploading handle.
		"""

		url = urlparse(self.path)
		path = os.path.normpath(url.path)
		self.dirname = os.path.dirname(path)
		self.filename = os.path.basename(path)

		# check meta - name, size, etc.
		if not self.check_meta():
			return

		# upload file
		f = open(os.path.join(tempfile.mkdtemp(), self.filename), "w")
		f.write(self.rfile.read(self.length))
		f.close()

		# check content - checksum, sign, etc.
		if not self.check_content(f.name):
			return

		# move to proper place
		shutil.move(f.name, os.path.join(self.dirname, self.filename))
		self.send_response(200)

	def check_meta(self):
		"""
		Check upload meta information.
		"""
		# check filename
		if not len(self.filename):
			self.send_error(400, 'No filename')
			return False

		# remove first / from dirname
		if os.path.isabs(self.dirname):
			self.dirname = self.dirname[1:]

		# check dirname
		if not os.path.isdir(self.dirname):
			self.send_error(400, 'Bad directory')
			# TODO allowed dirs check
			return False

		# existing file?
		if os.path.exists(os.path.join(self.dirname, self.filename)):
			self.send_error(400, 'File uploaded allready')
			return False

		# check if file should be stored
		if not self.filename.endswith(SIGNED):
			if not self.get_checksum():
				self.send_error(409, 'File not expected')
				return False

		return True

	def check_content(self, filename):
		"""
		Check file to be in .changes and having proper size.
		"""
		if self.filename.endswith(SIGNED):
			# TODO verify sign
			print 'TODO verify sign'

		else:
			f = open(filename, "r")
			md5 = hashlib.md5()
			md5.update(f.read(self.length))
			f.close()
			if md5.hexdigest() != self.md5:
				self.send_error(409, 'Checksum error');
				return False

		return True

	def get_checksum(self):
		"""
		Get self.file checksum from .changes file.
		"""
		pattern = "([0-9a-f]{32}) ([0-9]+) .* %s" % self.filename
		reg = re.compile(pattern)

		for changes in iglob(os.path.join(self.dirname, '*' + CHANGES)):
			if time.time() - os.path.getmtime(changes) > WINDOW:
				continue

			f = open(changes, "r")
			for line in f:
				line = line.strip()
				if not line.endswith(self.filename):
					continue

				try:
					m = reg.match(line)
					self.md5 = m.group(1)
					self.length = int(m.group(2))
					return True
				except AttributeError:
					continue

		return False

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

