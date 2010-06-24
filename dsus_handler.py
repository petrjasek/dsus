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
from BaseHTTPServer import BaseHTTPRequestHandler
from glob import iglob
from urlparse import urlparse
from tempfile import mkdtemp
from shutil import move
from time import time

CHANGES, COMMANDS = '.changes', '.commands'
SIGNED = (CHANGES, COMMANDS)

WINDOW = 3600 * 24 # secs we wait for files after .changes recieved

class DSUSHandler(BaseHTTPRequestHandler):
    """
    Handler for Debian Smart Upload Server Protocol.
    """

    dir = None
    file = None
    md5 = None
    length = 0

    def do_PUT(self):
        """ File uploading handle. """

        server_version = "DSUS/0.1"

        url = urlparse(self.path)
        path = os.path.normpath(url.path)
        self.dir = os.path.dirname(path)
        self.file = os.path.basename(path)
        self.length = int(self.headers["Content-Length"])

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
        """ Check file meta information. """

        # check filename
        if not self.file:
            self.send_error(400, 'No filename')
            return False

        # check directory
        if os.path.isabs(self.dir):
            self.dir = self.dir[1:]
        self.dir = os.path.join(self.server.cnf["DSUS::Path"], self.dir)
        if not os.path.isdir(self.dir):
            self.send_error(400, 'Bad directory')
            return False

        # check if file should be stored
        if not self.file.endswith(SIGNED):
            if not self.get_checksum():
                self.send_error(409, 'File not expected')
                return False

        return True

    def check_content(self, filename):
        """ Check file content. """

        if self.file.endswith(SIGNED):
            # TODO verify sign
            pass
        else:
            content = open(filename, "r")
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

        for changes in iglob(os.path.join(self.dir, '*' + CHANGES)):
            if time() - os.path.getmtime(changes) > WINDOW:
                continue
            file = open(changes, "r")
            for line in file:
                line = line.strip()
                if not line.endswith(self.file):
                    continue
                try:
                    match = reg.match(line)
                    if self.length != int(match.group(2)):
                        continue
                    self.md5 = match.group(1)
                    return True
                except AttributeError:
                    continue

        return False
