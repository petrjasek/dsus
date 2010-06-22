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
from BaseHTTPServer import HTTPServer

from daklib.config import Config
from dsus_handler import DSUSHandler

class DSUServer(HTTPServer):
	"""
	Debian Smart Upload Server class
	"""

	STATE_INIT = 0
	STATE_ACTIVE = 1
	STATE_SHUTDOWN = 2
	STATE_RECONFIG = 3

	def __init__(self):
		self.cnf = Config()
		self.address = ('', int(self.cnf["DSUS::port"]))
		HTTPServer.__init__(self, self.address, DSUSHandler)
		state = self.STATE_INIT


	def run(self):
		"""
		Server routine.
		"""
		# Set signals handles
		signal.signal(signal.SIGUSR1, self.handle_signal)
		signal.signal(signal.SIGHUP, self.handle_signal)

		# Run server
		self.state = self.STATE_ACTIVE
		while self.state == self.STATE_ACTIVE:
			self.cnf = Config()
			self.handle_request()


	def handle_signal(self, signum, frame):
		"""
		Change state with signals.
		"""
		print "Signal handle"
		if signum == signal.SIGUSR1:
			self.state = self.STATE_SHUTDOWN
			print "Server shutting down."
		elif signum == signal.SIGHUP:
			self.state = self.STATE_RECONFIG
			print "Config reloaded."


def usage():
	"""
	Print usage message.
	"""
	print "usage: dsus.py [-h|--help]"

def main(argv):
	"""
	Handles arguments and runs server.
	"""
	try:
		opts, args = getopt.getopt(argv, "h", ["help"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)

	# parse options
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()
			sys.exit()

	server = DSUServer()
	server.run()

if __name__ == "__main__":
	main(sys.argv[1:])

