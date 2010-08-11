#!/bin/sh

# Debian Smart Upload Client
# @copyright: 2010  Petr Jasek <jasekpetr@gmail.com>
# @license: GNU General Public License version 2 or later

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

CHANGES="$2"
SERVER="$1"

echo "uploading changes..."
curl -X PUT -T "$CHANGES" "$SERVER/$CHANGES?canges=$CHANGES" | grep "4[0-9]\{2\}"
if [ $? ]; then
    echo "Fix error and start upload again"
    exit
else
    echo "done"
fi

FILES=`grep '^ [a-f0-9]\{40\} [0-9]\+ [a-z0-9_.-]\+$' "$CHANGES" | cut -f 4 -d " "`
for FILE in $FILES; do
    echo "uploading $FILE..."
    CODE=0
    while [ $CODE -ne 1 ]; do
        curl -X PUT -T "$FILE" "$SERVER/$FILE?changes=$CHANGES" | grep "4[0-9][0-9]"
        CODE=$?
        if [ $CODE -ne 1 ]; then
            echo "Fix $FILE and press any key"
            read drop
        fi
    done
    echo "done"
done

curl -X PUT "$SERVER/?changes=$CHANGES&action=done"
echo "upload finished"
