#!/usr/bin/python

""" Debian Smart Upload Server checks

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
from time import time

from codes import *
import daklib.utils
from daklib.binary import Binary
from daklib.queue import Upload

class CheckError(Exception):
    """ Check error exception """
    def __init__(self, code):
        self.code = code
    def __str__(self):
        return self.code


def check_filename(handle):
    """ Filename must be non-empty """
    if not handle.filename:
        raise CheckError(FILENAME_EMPTY)
    return True

def check_headers(handle):
    """ Content-Length header must be specified """
    if not handle.headers.has_key("Content-Length"):
        raise CheckError(LENGTH_EMPTY)
    else:
        handle.length = int(handle.headers["Content-Length"])
    return True

def check_dirname(handle):
    """ Directory must exists if dirname is set """
    if os.path.isabs(handle.dirname):
        handle.dirname = handle.dirname[1:]
    handle.dest = os.path.join(handle.cnf["DSUS::Path"], handle.dirname)
    if not os.path.isdir(handle.dest):
        raise CheckError(DESTINATION_NOT_FOUND)
    return True

def check_changes(handle):
    """ Changes file must exists """
    handle.changes = os.path.join(handle.dest, handle.changes)
    if not os.path.isfile(handle.changes):
        raise CheckError(CHANGES_NOT_FOUND)
    handle.upload = Upload()
    if not handle.upload.load_changes(handle.changes):
        print handle.upload.rejects
        raise CheckError(CHANGES_BAD_FORMAT)
    if not handle.upload.pkg.files.has_key(handle.filename):
        raise CheckError(FILE_UNEXPECTED)
    else:
        handle.md5sum = handle.upload.pkg.files[handle.filename]['md5sum']
    return True

def check_time(handle):
    """ Check if upload is within time window """
    window  = int(handle.cnf['DSUS::timeWindow'])
    if time() - os.path.getmtime(handle.changes) > window:
        raise CheckError(SESSION_EXPIRED)
    return True

def check_checksum(handle):
    """ Checksum check """
    if not handle.md5sum:
        raise CheckError(FILE_UNEXPECTED)
    md5 = hashlib.md5()
    content = open(handle.tempfile.name, 'r')
    md5.update(content.read(handle.length))
    content.close()
    if md5.hexdigest() != handle.md5sum:
        raise CheckError(CHECKSUM_ERROR)
    return True

def check_valid_deb(handle):
    """ Check Binary.valid_deb """
    binary = Binary(handle.tempfile.name, handle.log_error)
    if not binary.valid_deb():
        raise CheckError(BINARY_ERROR)
    return True

def check_signature(handle):
    """ Check file signature """
    fingerprint, rejects = daklib.utils.check_signature(handle.tempfile.name)
    if not fingerprint:
        #print rejects.pop()
        raise CheckError(SIGNATURE_ERROR)
    return True
