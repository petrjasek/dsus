#!/usr/bin/python

""" Debian Smart Upload Server handler class

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

import os.path
import urlparse
import shutil
from time import strftime
from tempfile import mkdtemp
from BaseHTTPServer import BaseHTTPRequestHandler

from codes import *
from checks import *

class DSUSHandler(BaseHTTPRequestHandler):
    """
    Handler for Debian Smart Upload Server Protocol.
    """

    server_version = "DSUS/0.1"

    responses = responses # map codes.response to handle.responses

    error_message_format = "%(code)d: %(message)s (%(explain)s)\n"

    checks = {
        'changes': {
            'meta': ['filename', 'headers', 'dirname'],
            'content': ['signature'],
            },
        'deb': {
            'meta': ['filename', 'headers', 'dirname', 'changes', 'time', 'size'],
            'content': ['checksum', 'valid_deb', 'lintian'],
            },
        'default': {
            'meta': ['filename', 'headers', 'dirname', 'changes', 'time', 'size'],
            'content': ['checksum'],
            }
        }

    def do_PUT(self):
        """ File uploading handle. """
        # parse url
        url = urlparse.urlparse(self.path)
        params = urlparse.parse_qs(url.query)
        
        # extract path
        self.path = os.path.normpath(url.path)
        self.dirname = os.path.dirname(self.path)
        self.filename = os.path.basename(self.path)

        # set config for checks
        self.cnf = self.server.cnf

        # get changes
        try:
            self.changes = params["changes"].pop()
        except KeyError:
            self.send_error(CHANGES_EMPTY)
            return

        # get action
        try:
            action = params["action"].pop()
        except KeyError:
            action = "upload" # default

        if action == "done":
            self.action_done()
        elif action == "upload":
            self.action_upload()
        else:
            self.send_error(ACTION_UNKNOWN)

    def action_done(self):
        """
        Finishes upload session.
        """
        pass

    def action_upload(self):
        """
        Handles file upload.

        First it checks meta information - content-length, filename
        and directory. For files not in *.changes it looks into associated
        changes file if it should be uploaded.
        When it passes file is uploaded into temprary directory where
        various checks will be performed - verify sign for *.changes etc.
        If these are ok too file is moved into specified destination.
        On error it returns code and some meaningfull message to client.
        """
        # get type by extension
        self.type = self.filename.split('.').pop()
        if not self.checks.has_key(self.type):
            self.type = "default"

        if self.trigger_checks('meta'):
            return

        # upload file
        tempdir = mkdtemp()
        self.tempfile = open(os.path.join(tempdir, self.filename), 'w')
        self.tempfile.write(self.rfile.read(self.length))
        self.tempfile.close()

        if self.trigger_checks('content'):
            shutil.rmtree(tempdir)
            return

        # store file
        shutil.move(self.tempfile.name, os.path.join(self.dest, self.filename))
        shutil.rmtree(tempdir)
        self.send_response(OK)

    def trigger_checks(self, category):
        """ Triggers checks for given filetype and category """
        print 'trigger', category, 'for', self.filename
        for check in self.checks[self.type][category]:
            check = 'check_' + check
            try:
                globals()[check](self)
            except CheckError as e:
                print self.filename, check, 'raised error', e.code
                self.send_error(e.code)
                return e.code
            except KeyError:
                print check, 'not found'
            else:
                print self.filename, check, 'passed'
        return

    def log_message(self, format, *args):
        """ Logs message. """
        log = open(self.cnf["DSUS::LogFile"], 'a')
        log.write(strftime('[%d/%b/%Y:%H:%M:%S %Z] '))
        log.write(format % args)
        log.write("\n")
        log.close()
