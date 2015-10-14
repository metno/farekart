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

import os, sys, urllib2, urlparse
import datetime
import dateutil.parser, dateutil.tz
from lxml import etree
from PyRSS2Gen import RSS2, RSSItem

CAP_nsmap = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}

def parse_cap_file(cap_schema, cap_file = None, cap_text = None):

    if cap_file:
        # Parse and validate the CAP file.
        root = etree.parse(cap_file).getroot()
    elif cap_text:
        # Parse the CAP document.
        root = etree.fromstring(cap_text)
    
    if not cap_schema.validate(root):
        sys.stderr.write("Error: CAP file '%s' is not valid.\n" % cap_file)
        sys.exit(1)

    return root


def find_id_and_type(cap):

    identifier = cap.find('.//cap:identifier', CAP_nsmap).text
    msgType = cap.find('.//cap:msgType', CAP_nsmap).text
    return identifier, msgType


def find_latest_time(cap):

    expires_list = []
    for expires in cap.iterfind('.//cap:expires', CAP_nsmap):
        expires_list.append(dateutil.parser.parse(expires.text))
    
    return max(expires_list)


def find_cancel_references(cap):

    references = cap.find('.//cap:references', CAP_nsmap).text.strip().split()
    references = filter(lambda word: word, references)
    for ref in references:
    
        pieces = ref.split(",")
        if len(pieces) != 3:
            sys.stderr.write("Error: CAP file '%s' contains invalid cancellation references.\n" % file_name)
            sys.exit(1)
        
        sender, original_id, time = pieces
        yield original_id


def process_message(file_name, cap, items, cancel, order):

    identifier, msgType = find_id_and_type(cap)
    
    if msgType == "Cancel":
    
        # Record the relationship between messages in the cancellation dictionary.
        for original_id in find_cancel_references(cap):
            cancel.append((original_id, identifier))
    
    items[identifier] = (msgType, cap)
    order.append((identifier, file_name))


def expire_message(expiry_time, identifier, msgType, cap):

    # Find the latest expiry time in the file.
    latest = find_latest_time(cap)
    
    # Discard the item if the corresponding CAP document has expired.
    if latest <= expiry_time:
        return True
    
    return False
    

def parse_index_file(index_schema, cap_schema, index_file):
    """Parses the given index_file, returning a message dictionary, a cancellation
    dictionary and a list of identifiers and file names in the order in which
    they appeared in the index file.
    
    Uses the cap_schema and index_schema to validate CAP and MIfare index files
    respectively.

    The message dictionary maps the identifier of each CAP file to the CAP
    document itself. The cancellation dictionary maps identifiers of
    messages that should be cancelled to the cancellation message identifier.
    
    Since these messages have not been published, any that have corresponding
    cancellation messages, and the cancellations themselves, are not included
    in the message dictionary."""

    try:
        tree = etree.parse(index_file)
    except etree.XMLSyntaxError:
        sys.stderr.write("Error: index file '%s' is not well-formed.\n" % index_file)
        sys.exit(1)
    
    if not index_schema.validate(tree):
        sys.stderr.write("Error: index file '%s' is not valid.\n" % index_file)
        sys.exit(1)
    
    index_dir = os.path.split(index_file)[0]

    # Create a dictionary mapping identifiers to tuples containing message types
    # and CAP documents.
    items = {}
    # Create a list mapping cancelled message identifiers to the identifiers
    # of the Cancel messages that refer to them.
    cancel = []
    # Maintain the order of the messages and their file names.
    order = []

    for element in tree.iterfind('.//file'):

        valid_from = dateutil.parser.parse(element.get('valid_from'))
        valid_to = dateutil.parser.parse(element.get('valid_to'))

        # The file name is relative to the index file, so obtain an absolute path.
        file_name = element.text
        file_path = os.path.join(index_dir, file_name)
        
        try:
            cap = parse_cap_file(cap_schema, cap_file = file_path)
        except etree.XMLSyntaxError:
            sys.stderr.write("Error: CAP file '%s' is not valid.\n" % file_path)
            sys.exit(1)
        
        process_message(file_name, cap, items, cancel, order)
    
    for reference_id, cancel_id in cancel:

        # If the identifier referred to by the Cancel message is in the index
        # then remove it before it is sent. Also remove the Cancel message.
        if reference_id in items:
            sys.stdout.write("Cancelling message '%s' before it can be sent.\n" % reference_id)
            del items[reference_id]
            del items[cancel_id]
    
    return items, cancel, order


def parse_rss_file(cap_schema, rss_file):
    """Parses the given rss_file, returning a message dictionary, a cancellation
    dictionary and a list of identifiers and file names in the order in which
    they appeared in the RSS file.
    
    Uses the cap_schema to validate CAP files that are read to obtain additional
    information that is not supplied in the RSS file.

    The message dictionary maps the identifier of each CAP file to the CAP
    document itself. The cancellation dictionary maps identifiers of
    messages that should be cancelled to the cancellation message identifier."""

    try:
        rss = etree.parse(rss_file)
    except etree.XMLSyntaxError:
        sys.stderr.write("Error: RSS file '%s' is not valid.\n" % index_file)
        sys.exit(1)
    
    # Create a dictionary mapping identifiers to tuples containing message types
    # and CAP documents.
    items = {}
    # Create a list mapping cancelled message identifiers to the identifiers
    # of the Cancel messages that refer to them.
    cancel = []
    # Maintain the order of the messages and their file names.
    order = []
    
    for element in rss.iterfind('.//item'):
    
        # Fetch the CAP file referred to by the RSS feed.
        url = element.find('.//link').text
        try:
            u = urllib2.urlopen(url)
            cap_text = u.read()
            u.close()
        except urllib2.HTTPError:
            sys.stderr.write("Error: failed to fetch CAP file '%s' specified in RSS file '%s'.\n" % (url, rss_file))
            sys.exit(1)
        
        try:
            cap = parse_cap_file(cap_schema, cap_text = cap_text)
        except etree.XMLSyntaxError:
            sys.stderr.write("Warning: failed to obtain CAP file from URL '%s'.\n" % item.link)
            continue
        
        process_message(item.link, cap, items, cancel, order)
    
    return items, cancel, order


if __name__ == "__main__":

    if len(sys.argv) != 5:

        sys.stderr.write(__doc__)
        sys.exit(1)
    
    index_file = sys.argv[1]
    rss_file = sys.argv[2]
    output_dir = sys.argv[3]
    base_url = sys.argv[4]
    
    # Get the current time.
    now = datetime.datetime.now(dateutil.tz.tzutc())

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # Load the index schema.
    index_schema_doc = etree.parse(os.path.join("schemas", "mifare-index.xsd"))
    index_schema = etree.XMLSchema(index_schema_doc)

    # Load the CAP schema.
    cap_schema_doc = etree.parse(os.path.join("schemas", "CAP-v1.2.xsd"))
    cap_schema = etree.XMLSchema(cap_schema_doc)

    # Parse and validate the index file.
    items, cancel, order = parse_index_file(index_schema, cap_schema, index_file)
    
    # Parse the RSS file, if found.
    if os.path.exists(rss_file):
        rss_items, rss_cancel, rss_order = parse_rss_file(cap_schema, rss_file)
        
        # Merge the item dictionaries from the RSS and index files.
        items.update(rss_items)

        # Append the new cancellations to the old ones.
        cancel = rss_cancel + cancel
        
        # Append the new identifiers to the old ones.
        order = rss_order + order
    
    # At this point, we should only have new alerts and new cancellations
    # from the index and old alerts and cancellations from the RSS file.
    
    # Check for expired messages and remove them, removing any cancellations
    # that refer to them. We cannot remove messages with cancellations that
    # are still valid since users may have only read the original messages.
    
    # Maintain a set of expired cancellations.
    expired = set()
    new_items = []

    for identifier, file_name in order:
    
        msgType, cap = items[identifier]
        if msgType == "Alert":

            if expire_message(now, identifier, msgType, cap):

                # Expire the message (do not include it in the new list).
                if identifier in cancel:
                    # Also expire the cancellation.
                    expired.add(cancel[identifier])
            else:
                new_items.append((file_name, cap))

        elif msgType == "Cancel":

            if identifier not in expired:
                new_items.append((file_name, cap))
    
    new_rss_items = []

    for file_name, cap in new_items:
    
        # Check if the file name is actually a URL.
        if "/" in file_name:
            url = file_name
        else:
            url = urlparse.urljoin(base_url, file_name)

        new_rss_items.append(RSSItem(
            title = cap.find('.//cap:headline', CAP_nsmap).text,
            link = url,
            description = cap.find('.//cap:description', CAP_nsmap).text,
            guid = cap.find('.//cap:identifier', CAP_nsmap).text,
            pubDate = cap.find('.//cap:sent', CAP_nsmap).text,
            author = cap.find('.//cap:sender', CAP_nsmap).text,
            categories = [cap.find('.//cap:category', CAP_nsmap).text]
            ))
    
    # Create a RSS feed.
    rss = RSS2(title = "Weather alerts",
               link = base_url,
               description = "Weather alerts from the Norwegian Meteorological Institute",
               lastBuildDate = now, items = new_rss_items)
    
    rss.write_xml(open(rss_file, "w"))
    sys.exit()
