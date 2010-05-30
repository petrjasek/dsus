#!/usr/bin/env python

import BaseHTTPServer

SERVER_ADDRESS = 8000

class DSUSHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	'''
	Handler for Debian Smart Upload Server Protocol.
	'''

	server_version = 'DSUS/0.1'

	def do_GET(self):
		'''
		Command handle.
		'''
		self.send_response(200, 'OK')
		self.end_headers()
	
	def du_PUT(self):
		'''
		File uploading handle.
		'''
		self.send_response(200, 'OK')


def run(server_class=BaseHTTPServer.HTTPServer,
		handler_class=BaseHTTPServer.BaseHTTPRequestHandler):
	'''
	Run server and handles signals.
	'''
	server_address = ('', SERVER_ADDRESS)
	httpd = server_class(server_address, handler_class)
	while 1 == 1:
		httpd.handle_request()


if __name == '__main__':
	run(handler_class=DSUSHandler)

