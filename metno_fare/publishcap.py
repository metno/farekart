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

"""Provides functions to manage publication of a collection of Common Alerting
Protocol (CAP) files specified by an index file as a Really Simple Syndication
(RSS) 2 file, using a base URL to refer to the CAP files in their final
location on a server.

Copies the CAP files and the RSS file to the output directory given.

"""

import datetime
import glob
import json
import os
import shutil
import urlparse

import dateutil.parser
import dateutil.tz
from lxml import etree
from lxml.etree import Element, ElementTree, SubElement

default_language = "no"

def parse_cap_file(cap_file = None, cap_text = None):
    """Parses the CAP document supplied by the file, cap_file, or passed as a
    string, cap_text, and validates it againts the schema, cap_schema.

    Returns the root element if successful or raises a ValueError exception
    if not."""

    cap_schema_doc = etree.parse(os.path.join(schema_dirname, "CAP-v1.2.xsd"))
    cap_schema = etree.XMLSchema(cap_schema_doc)

    if cap_file:
        # Parse and validate the CAP file.
        root = etree.parse(cap_file).getroot()
    elif cap_text:
        # Parse the CAP document.
        root = etree.fromstring(cap_text)
    
    if not cap_schema.validate(root):
        raise ValueError
    
    return root


def main(output_dir):
    """Controls the overall processing of CAP and index files to create an RSS feed.
    The given args are the arguments supplied by the user on the command line."""

    # Get the current time.
    now = datetime.datetime.now(dateutil.tz.tzutc())

    rss_file = "CAP.rss"
    base_url = os.getenv("CAP_BASE_URL", "http://api.met.no/CAP")

    # Ensure that the base URL ends with a trailing slash.
    if not base_url.endswith("/"):
        base_url += "/"

    languages = set(['en','no'])

    # Create feeds and channels for the languages used.

    for lang in languages:
    
        rss = Element('rss')
        rss.set('version', '2.0')

        channel = SubElement(rss, 'channel')
        SubElement(channel, 'title').text = "Weather alerts (%s)" % lang
        SubElement(channel, 'link').text = base_url
        SubElement(channel, 'description').text = "Weather alerts from the Norwegian Meteorological Institute"
        SubElement(channel, 'language').text = lang
        SubElement(channel, 'lastBuildDate').text = now.strftime('%Y-%m-%d %H:%M:%S UTC')

        jsonfile = os.path.join(output_dir, "CAP_%s.json" % lang)

        with open(jsonfile) as data_file:
            caplist = json.load(data_file)

        for cap in caplist:

            # Do not show  CAP file in feed
            if dateutil.parser.parse(cap['t_expires'])<= now:
                continue

            if cap.get('ref_by') is not None:
                continue

            item = SubElement(channel, 'item')
            SubElement(item, 'title').text = cap['title']
            url = urlparse.urljoin(base_url, cap['file'])
            SubElement(item, 'link').text = url
            SubElement(item, 'description').text = etree.CDATA(cap['description'])
            SubElement(item, 'guid').text =cap['id']
            SubElement(item, 'pubDate').text = cap['t_published']
            SubElement(item, 'author').text = "noreply@met.no"
            SubElement(item, 'category').text = "Met"
    
        # Write the new RSS feed files to the local output directory and copy them to the publishing directory.

        if lang == default_language:
            rss_lang_file = rss_file
        else:
            stem, suffix = os.path.splitext(rss_file)
            rss_lang_file = stem + '-' + lang + suffix

        f = open(os.path.join(output_dir, rss_lang_file), 'wb')
        ElementTree(rss).write(f, encoding='UTF-8', xml_declaration=True, pretty_print=True)
        f.close()


