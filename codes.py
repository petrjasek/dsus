#!/usr/bin/python

""" Debian Smart Upload Server Return Codes

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

# successfull
OK = 200

# errors pre-upload
CHANGES_EMPTY = 431
ACTION_UNKNOWN = 432
FILENAME_EMPTY = 433
DESTINATION_ERROR = 434
CHANGES_NOT_FOUND = 435
SESSION_EXPIRED = 436
LENGTH_EMPTY = 437
LENGTH_CONFLICT = 438
FILE_UNEXPECTED = 439

# errors post-upload
CHECKSUM_ERROR = 451
BINARY_ERROR = 452
SIGNATURE_ERROR = 453

responses = {
        200: ('OK', 'OK'),

        431: ('Empty changes', 'Changes param not specified'),
        432: ('Unknown action', 'Unknown action'),
        433: ('Empty filename', 'Filename not specified'),
        434: ('Destination error', 'Destination directory not found'),
        435: ('Changes not found', 'Changes file not found'),
        436: ('Session expired', 'Upload session expired'),
        437: ('Length empty', 'Content-Length header not specified'),
        438: ('Length conflict', 'Length header not match .changes'),
        439: ('File unexpected', 'Send .changes file first'),

        451: ('Checksum error', 'Checksum not match .changes'),
        452: ('Binary error', 'Binary error'),
        453: ('Signature error', 'Key not found in the keyring')
    }
