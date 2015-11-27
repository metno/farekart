#!/usr/bin/env python

# Copyright (C) 2015 MET Norway
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""Usage: metno-publish-cap.py <index file> <RSS file> <output directory> <target base URL for CAP files>

Publishes a collection of Common Alerting Protocol (CAP) files specified by an
index file as a Really Simple Syndication (RSS) 2 file, using the base URL to
refer to the CAP files in their final location on a server.

Copies the CAP files and the RSS file to the output directory given.

If an RSS file already exists, it will be updated with new items for the CAP
files supplied and expired items will be removed from the list it contains.
"""

import sys
from metno_fare import publishcap

if __name__ == "__main__":

    if len(sys.argv) != 5:
        sys.stderr.write(__doc__)
        sys.exit(1)

    index_file = sys.argv[1]
    rss_file = sys.argv[2]
    output_dir = sys.argv[3]
    base_url = sys.argv[4]

    publishcap.main(index_file, rss_file, output_dir, base_url)

    sys.exit()
