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

import re
import os.path
import hashlib
import urlparse
from BaseHTTPServer import BaseHTTPRequestHandler
from shutil import move
import time
from tempfile import NamedTemporaryFile

from daklib.binary import Binary
from daklib.queue import Upload

from codes import *

# important extensions
CHANGES, COMMANDS = '.changes', '.commands'
SIGNED = (CHANGES, COMMANDS)

class DSUSHandler(BaseHTTPRequestHandler):
    """
    Handler for Debian Smart Upload Server Protocol.
    """

    server_version = "DSUS/0.1"

    # set response codes
    responses = responses

    error_message_format = "%(code)d: %(message)s (%(explain)s)\n"

    def do_PUT(self):
        """ File uploading handle. """
        # parse url
        url = urlparse.urlparse(self.path)
        params = urlparse.parse_qs(url.query)
        
        # extract path
        self.path = os.path.normpath(url.path)
        self.dirname = os.path.dirname(self.path)
        self.filename = os.path.basename(self.path)

        # get changes
        try:
            self.changes = params["changes"].pop()
        except KeyError:
            self.send_error(CHANGES_EMPTY)
            return

        # get action
        action = "upload" # default
        if params.has_key("action"):
            action = params["action"].pop()

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
        # common pre-upload checks
        if not self.filename:
            self.send_error(FILENAME_EMPTY)
            return

        if not self.headers.has_key("Content-Length"):
            self.send_error(LENGTH_EMPTY)
            return
        else:
            self.length = int(self.headers["Content-Length"])

        if os.path.isabs(self.dirname):
            self.dirname = self.dirname[1:]
        dest = os.path.join(self.server.cnf["DSUS::Path"], self.dirname)
        if not os.path.isdir(dest):
            self.send_error(DESTINATION_NOT_FOUND)
            return

        if self.filename.endswith(SIGNED):
            # TODO signed file checks
            pass
        else:
            changes = os.path.join(dest, self.changes)
            if not os.path.isfile(changes):
                self.send_error(CHANGES_NOT_FOUND)
                return

            upload = Upload()
            if not upload.load_changes(changes):
                print upload.rejects
                return

            window = int(self.server.cnf["DSUS::UploadWindow"])
            if time.time() - os.path.getmtime(changes) > window:
                self.send_error(SESSION_EXPIRED)
                return

            checksum = None
            pattern = "([0-9a-f]{32}) ([0-9]+) .* %s" % self.filename
            reg = re.compile(pattern)
            changes_handle = open(changes, 'r')
            for line in changes_handle:
                match = reg.match(line)
                if match:
                    if length != int(match.group(2)):
                        self.send_error(LENGTH_CONFLICT)
                        return
                    checksum = match.group(1)
                    break
            if not checksum:
                self.send_error(FILE_UNEXPECTED)
                return

        # upload file
        tmp_file = NamedTemporaryFile(suffix='.' + self.filename.split('.')[-1])
        tmp_file.write(self.rfile.read(self.length))
        tmp_file.flush()

        # content checks
        if self.filename.endswith(SIGNED):
            # TODO signed file content checks
            pass
        else:
            if checksum != self.get_md5(tmp_file, self.length):
                self.send_error(CHECKSUM_CONFLICT)
                return

            binary = Binary(tmp_file.name, self.log_error)
            if not binary.valid_deb():
                self.send_error(BINARY_ERROR)
                return
            # TODO more checks (lintian, etc.)

        # store file
        tmp_file.seek(0)
        out_file = open(os.path.join(dest, self.filename), 'w')
        out_file.write(tmp_file.read(self.length))
        out_file.close()
        self.send_response(OK)

    def get_md5(self, file, length):
        """ Counts MD5 checksum for given file. """
        file.seek(0)
        md5 = hashlib.md5()
        md5.update(file.read(length))
        return md5.hexdigest()

    def log_message(self, format, *args):
        """ Logs message. """
        log = open(self.server.cnf["DSUS::LogFile"], 'a')
        log.write(time.strftime('[%d/%b/%Y:%H:%M:%S %Z] '))
        log.write(format % args)
        log.write("\n")
        log.close()
