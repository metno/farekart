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

from collections import OrderedDict
import os, shutil, sys, urllib2, urlparse
import datetime
import dateutil.parser, dateutil.tz
from lxml.etree import Element, ElementTree, SubElement
from lxml import etree
import json

CAP_nsmap = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}
default_language = "no"

def parse_cap_file(cap_schema, cap_file = None, cap_text = None):
    """Parses the CAP document supplied by the file, cap_file, or passed as a
    string, cap_text, and validates it againts the schema, cap_schema.

    Returns the root element if successful or raises a ValueError exception
    if not."""

    if cap_file:
        # Parse and validate the CAP file.
        root = etree.parse(cap_file).getroot()
    elif cap_text:
        # Parse the CAP document.
        root = etree.fromstring(cap_text)
    
    if not cap_schema.validate(root):
        raise ValueError
    
    return root


def find_id_and_type(cap):
    """Returns the identifier and message type for the CAP document given by cap."""

    identifier = cap.find('.//cap:identifier', CAP_nsmap).text
    msgType = cap.find('.//cap:msgType', CAP_nsmap).text
    return identifier, msgType


def find_latest_time(cap):
    """Finds the latest expiry time in a CAP document given by cap."""

    expires_list = []
    for expires in cap.iterfind('.//cap:expires', CAP_nsmap):
        expires_list.append(dateutil.parser.parse(expires.text))
    
    return max(expires_list)


def find_references(cap, file_name):
    """Finds the references in a CAP document, cap, and yields each identifier
    in turn."""

    references = cap.find('.//cap:references', CAP_nsmap).text.strip().split()
    references = filter(lambda word: word, references)
    for ref in references:
    
        pieces = ref.split(",")
        if len(pieces) != 3:
            sys.stderr.write("Error: CAP file '%s' contains invalid cancellation references.\n" % file_name)
            sys.exit(1)
        
        sender, original_id, time = pieces
        yield original_id


def process_message(file_name, cap, messages, cancel, update):
    """Processes the CAP message, cap, with the associated file_name, updating
    the message and cancellation dictionaries.
    
    Messages that are identified as duplicates are discarded."""

    identifier, msgType = find_id_and_type(cap)
    
    if identifier in messages:
        # Check for duplicate messages.
        sys.stderr.write("Warning: CAP file '%s' has identifier '%s' that has already been registered. Skipping.\n" % (file_name, identifier))
    
    elif msgType == "Cancel":
    
        # Record the relationship between messages in the cancellation dictionary.
        for original_id in find_references(cap, file_name):
            cancel[original_id] = identifier
    
    elif msgType == "Update":

        # Record the relationship between messages in the update dictionary.
        for original_id in find_references(cap, file_name):
            update[original_id] = identifier

    messages[identifier] = (msgType, file_name, cap)


def update_message(messages, reference_id, update_id):
    return
    msgType, file_name, cap = messages[update_id]
    
    # Convert the Update message into an Alert message.
    cap.find('.//cap:msgType', CAP_nsmap).text = "Alert"

    # Remove the references element.
    references = cap.find('.//cap:references', CAP_nsmap)
    alert = references.getparent()
    alert.remove(references)


def expire_message(expiry_time, cap):
    """Returns True if the CAP document, cap, has a latest expiry time that is
    earlier than the given expiry_time, or returns False if the document is
    still valid."""

    # Find the latest expiry time in the file.
    latest = find_latest_time(cap)
    
    # Discard the item if the corresponding CAP document has expired.
    if latest <= expiry_time:
        return True
    
    return False


def parse_index_file(index_schema, cap_schema, index_file):
    """Parses the given index_file, returning message, cancellation and update
    dictionaries. The message dictionary contains messages in the order in
    which they appeared in the index file.
    
    Uses the cap_schema and index_schema to validate CAP and MIfare index files
    respectively.

    The message dictionary maps the identifier of each CAP file to the message
    type, file name and CAP document itself. The cancellation dictionary maps
    identifiers of messages that should be cancelled to the corresponding
    cancellation message identifiers.
    
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

    # Create a dictionary mapping identifiers to tuples containing message types,
    # file names and CAP documents.
    messages = OrderedDict()
    # Create a dictionary mapping cancelled message identifiers to the identifiers
    # of the Cancel messages that refer to them, and a dictionary mapping updated
    # messages to the Update messages that refer to them.
    cancel = {}
    update = {}

    for element in tree.iterfind('.//file'):

        # The file name is relative to the index file, so obtain an absolute path.
        file_name = element.text
        file_path = os.path.join(index_dir, file_name)
        
        try:
            cap = parse_cap_file(cap_schema, cap_file = file_path)
        except (ValueError, etree.XMLSyntaxError):
            sys.stderr.write("Error: CAP file '%s' is not valid.\n" % file_path)
            sys.exit(1)
        
        process_message(file_name, cap, messages, cancel, update)

    return messages, cancel, update


def main(index_file, rss_file, output_dir, publish_dir, base_url):
    """Controls the overall processing of CAP and index files to create an RSS feed.
    The given args are the arguments supplied by the user on the command line."""

    # Get the current time.
    now = datetime.datetime.now(dateutil.tz.tzutc())

    if not os.path.exists(publish_dir):
        os.mkdir(publish_dir)

    if os.path.exists("schemas"):
        schema_dirname = "schemas"
    else:
        schema_dirname = "/usr/share/xml/farekart"

    # Ensure that the base URL ends with a trailing slash.
    if not base_url.endswith("/"):
        base_url += "/"

    # Load the index schema.
    index_schema_doc = etree.parse(os.path.join(schema_dirname, "mifare-index.xsd"))
    index_schema = etree.XMLSchema(index_schema_doc)

    # Load the CAP schema. Files already validated
    cap_schema_doc = etree.parse(os.path.join(schema_dirname, "CAP-v1.2.xsd"))
    cap_schema = etree.XMLSchema(cap_schema_doc)

    # Parse and validate the index file.
    messages, cancel, update = parse_index_file(index_schema, cap_schema, index_file)

    new_messages = []
    archive_messages = []

    for identifier in messages:
    
        try:
            msgType, file_name, cap = messages[identifier]
        except KeyError:
            continue

        if not expire_message(now, cap):
            new_messages.append((file_name, cap))

    # Republish the CAP files to the publishing directory.
    # Note that we cannot just copy the files because some Update messages may
    # have been converted to Alert messages.
    # TODO, this files can now be copied

    for file_name, cap in new_messages:

        if urlparse.urlparse(file_name).scheme != "":
            file_name = urlparse.urlparse(file_name).path.split('/')[-1]

        f = open(os.path.join(publish_dir, file_name), 'wb')
        ElementTree(cap).write(f, encoding="UTF-8", xml_declaration=True,
                                  standalone=True, pretty_print=True)
        f.close()
    
    # Find the languages used in the CAP files.
    languages = set(['en','no'])
    for file_name, cap in new_messages:
        for lang in cap.findall('.//cap:language', CAP_nsmap):
            languages.add(lang.text.strip())

    # Create feeds and channels for the languages used.
    feeds = {}
    caplist = {}

    for lang in languages:
    
        rss = Element('rss')
        rss.set('version', '2.0')

        channel = SubElement(rss, 'channel')
        SubElement(channel, 'title').text = "Weather alerts (%s)" % lang
        SubElement(channel, 'link').text = base_url
        SubElement(channel, 'description').text = "Weather alerts from the Norwegian Meteorological Institute"
        SubElement(channel, 'language').text = lang
        SubElement(channel, 'lastBuildDate').text = now.strftime('%Y-%m-%d %H:%M:%S UTC')

        feeds[lang] = (rss, channel)
        jsonfile = os.path.join(output_dir, "CAP_%s.json" % lang)


        with open(jsonfile) as data_file:
            caplist[lang] = json.load(data_file)

        rss, channel = feeds[lang]

        for cap in caplist[lang]:

            identifier = cap['id']
            msgType, file_name, capxml = messages[identifier]
            if expire_message(now, capxml):
                continue

            item = SubElement(channel, 'item')
            SubElement(item, 'title').text = cap['title']
            url = urlparse.urljoin(base_url, cap['file'])
            SubElement(item, 'link').text = url
            SubElement(item, 'description').text = etree.CDATA(cap['description'])
            SubElement(item, 'guid').text =identifier
            SubElement(item, 'pubDate').text = cap['t_published']
            SubElement(item, 'author').text = "noreply@met.no"
            SubElement(item, 'category').text = "Met"
    
        # Write the new RSS feed files to the local output directory so that they can be read
        # next time, and copy them to the publishing directory.

    for lang in languages:

        if lang == default_language:
            rss_lang_file = rss_file
        else:
            stem, suffix = os.path.splitext(rss_file)
            rss_lang_file = stem + '-' + lang + suffix

        rss, channel = feeds[lang]

        f = open(os.path.join(output_dir, rss_lang_file), 'wb')
        ElementTree(rss).write(f, encoding='UTF-8', xml_declaration=True, pretty_print=True)
        f.close()

        if output_dir != publish_dir:
            shutil.copy2(os.path.join(output_dir, rss_lang_file), os.path.join(publish_dir, rss_lang_file))


