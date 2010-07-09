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
from glob import iglob
from tempfile import mkdtemp
from shutil import move
from time import time

from daklib.binary import Binary
from daklib.queue import Upload

# status codes
# successfull
OK = 200

# errors pre-upload
CHANGES_EMPTY = 431
ACTION_UNKNOWN = 432
FILENAME_EMPTY = 433
DESTINATION_ERROR = 434
CHANGES_NOT_FOUND = 435
SESSION_EXPIRED = 436

# important extensions
CHANGES, COMMANDS = '.changes', '.commands'
SIGNED = (CHANGES, COMMANDS)

class DSUSHandler(BaseHTTPRequestHandler):
    """
    Handler for Debian Smart Upload Server Protocol.
    """

    server_version = "DSUS/0.1"

    # mapping codes to messages
    responses = {
        200: ('OK', 'OK'),

        431: ('Empty changes', 'Changes param not specified'),
        432: ('Unknown action', 'Unknown action'),
        433: ('Empty filename', 'Filename not specified'),
        434: ('Destination error', 'Destination directory not found'),
        435: ('Changes not found', 'Changes file not found'),
        436: ('Session expired', 'Upload session expired'),
    }

    def do_PUT(self):
        """ File uploading handle. """
        # parse url
        url = urlparse.urlparse(self.path)
        path = os.path.normpath(url.path)
        params = urlparse.parse_qs(url.query)
        dirname = os.path.dirname(path)
        filename = os.path.basename(path)

        if not params.has_key("changes"):
            # changes params required
            self.send_error(CHANGES_EMPTY)
            return
        else:
            changes = params["changes"].pop()

        if params.has_key("action"):
            action = params["action"]
        else:
            action = ["upload"] # default

        if "done" in action:
            self.handle_done(changes, dirname)
        elif "upload" in action:
            self.handle_upload(changes, dirname, filename)
        else:
            self.send_error(ACTION_UNKNOWN)

    def handle_done(self, changes, dirname):
        """
        Finishes upload session.

        @type changes: string
        @param changes: .changes file with everything uploaded

        @type dirname: string
        @param dirname: dirname containing changes file
        """
        pass

    def handle_upload(self, changes, dirname, filename):
        """
        Handles file upload.

        First it checks meta information - content-length, filename
        and directory. For files not in *.changes it looks into associated
        changes file if it should be uploaded.
        When it passes file is uploaded into temprary directory where
        various checks will be performed - verify sign for *.changes etc.
        If these are ok too file is moved into specified destination.
        On error it returns code and some meaningfull message to client.

        @type changes: string
        @param changes: .changes file

        @type dirname: string
        @param dirname: destination path

        @type filename: string
        @param filename: target filename
        """
        # common pre-upload checks
        if not filename:
            self.send_error(FILENAME_EMPTY)
            return

        if not self.headers.has_key("Content-Length"):
            self.send_error(LENGTH_EMPTY)
            return
        else:
            length = int(self.headers["Content-Length"])

        if os.path.isabs(dirname):
            dirname = dirname[1:]
        dest = os.path.join(self.server.cnf["DSUS::Path"], dirname)
        if not os.path.isdir(dest):
            self.send_error(DESTINATION_NOT_FOUND)
            return

        if filename.endswith(SIGNED):
            # TODO signed file checks
            pass
        else:
            changes = os.path.join(dest, changes)
            if not os.path.isfile(changes):
                self.send_error(CHANGES_NOT_FOUND)
                return

            window = int(self.server.cnf["DSUS::UploadWindow"])
            if time() - os.path.getmtime(changes) > window:
                self.send_error(SESSION_EXPIRED)
                return

        # upload file
        tmp_file = open(os.path.join(mkdtemp(), filename), "w")
        tmp_file.write(self.rfile.read(length))
        tmp_file.close()

        # content checks
        if filename.endswith(SIGNED):
            # TODO signed file content checks
            pass
        else:
            binary = Binary(tmp_file.name, self.log_error)
            if not binary.valid_deb():
                self.send_error(400, "Not valid")
                return
            # TODO other checks (lintian etc.)
            pass

        # store file
        move(tmp_file.name, os.path.join(dest, filename))
        self.send_response(OK)

    def log_message(self, format, *args):
        """ Logs message. """
        log = open(self.server.cnf["DSUS::LogFile"], 'a')
        log.write(format % args)
        log.write("\n")
        log.close()

    ##########

    def check_content(self, filename):
        """ Check file content. """
        if self.file.endswith(SIGNED):
            # TODO verify sign
            pass
        else:
            content = open(filename, 'r')
            md5 = hashlib.md5()
            md5.update(content.read(self.length))
            content.close()
            if md5.hexdigest() != self.md5:
                self.send_error(409, 'Checksum error');
                return False

        return True

    def get_checksum(self):
        """ Get checksum for file from .changes. """
        pattern = "([0-9a-f]{32}) ([0-9]+) .* %s" % self.file
        reg = re.compile(pattern)

        match = reg.match(line)
        self.md5 = match.group(1)
        return True
