#!/usr/bin/env python

import BaseHTTPServer

class DSUSHandler(BaseHTTPServer.BaseHTTPRequestHandler):

	server_version = 'DSUS/0.1'

	def do_GET(self):
		print self.headers
		self.send_response(200, 'OK')
		self.send_header('Message', 'HI')
		self.end_headers()

def run(server_class=BaseHTTPServer.HTTPServer,
		handler_class=BaseHTTPServer.BaseHTTPRequestHandler):
	"""
	Run server until get some signal to stop.
	"""
	server_address = ('', 8000)
	httpd = server_class(server_address, handler_class)
	while 1 == 1:
		httpd.handle_request()


if __name == '__main__':
	run(handler_class=DSUSHandler)

