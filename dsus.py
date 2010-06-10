#!/usr/bin/env python

""" Debian Smart Upload Server """

from glob import iglob
from urlparse import urlparse
from tempfile import mkdtemp
from shutil import move
from time import time
import sys, getopt, signal, os.path
import re, hashlib
import BaseHTTPServer

SERVER_VERSION = "DSUS/0.1"

config = {
	"port": 8000,
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

	dir = None
	file = None
	md5 = None
	length = 0

	def do_PUT(self):
		"""
		File uploading handle.
		"""

		url = urlparse(self.path)
		path = os.path.normpath(url.path)
		self.dir = os.path.dirname(path)
		self.file = os.path.basename(path)

		# check meta - name, size, etc.
		if not self.check_meta():
			return

		# upload file
		f = open(os.path.join(mkdtemp(), self.file), "w")
		f.write(self.rfile.read(self.length))
		f.close()

		# check content - checksum, sign, etc.
		if not self.check_content(f.name):
			return

		# store file
		move(f.name, os.path.join(self.dir, self.file))
		self.send_response(200)

	def check_meta(self):
		"""
		Check file meta information.
		"""
		# check filename
		if not len(self.file):
			self.send_error(400, 'No filename')
			return False

		# filter abs dir
		if os.path.isabs(self.dir):
			self.dir = self.dir[1:]

		# check dirname
		if not os.path.isdir(self.dir):
			self.send_error(400, 'Bad directory')
			# TODO allowed dirs check
			return False

		# existing file?
		if os.path.exists(os.path.join(self.dir, self.file)):
			self.send_error(400, 'File uploaded allready')
			return False

		# check if file should be stored
		if not self.file.endswith(SIGNED):
			if not self.get_checksum():
				self.send_error(409, 'File not expected')
				return False

		return True

	def check_content(self, filename):
		"""
		Check file content.
		"""
		if self.file.endswith(SIGNED):
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
		Get checksum for file from .changes.
		"""
		pattern = "([0-9a-f]{32}) ([0-9]+) .* %s" % self.file
		reg = re.compile(pattern)

		for changes in iglob(os.path.join(self.dir, '*' + CHANGES)):
			if time() - os.path.getmtime(changes) > WINDOW:
				continue

			f = open(changes, "r")
			for line in f:
				line = line.strip()
				if not line.endswith(self.file):
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

