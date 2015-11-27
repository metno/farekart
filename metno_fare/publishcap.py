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

Uses an existing RSS file, if present, which will be updated with new items
for new CAP files and cleared of expired items.
"""

from collections import OrderedDict
import os, shutil, sys, urllib2, urlparse
import datetime
import dateutil.parser, dateutil.tz
from lxml.etree import Element, ElementTree, SubElement
from lxml import etree

CAP_nsmap = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}

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
    
    # Check for duplicate messages.
    if identifier in messages:
        sys.stderr.write("Warning: CAP file '%s' has identifier '%s' that has already been registered. Skipping.\n" % (file_name, identifier))
        return
    
    if msgType == "Cancel":
    
        # Record the relationship between messages in the cancellation dictionary.
        for original_id in find_references(cap, file_name):
            cancel[original_id] = identifier
    
    elif msgType == "Update":

        # Record the relationship between messages in the update dictionary.
        for original_id in find_references(cap, file_name):
            update[original_id] = identifier

    messages[identifier] = (msgType, file_name, cap)


def update_message(messages, update, reference_id, update_id):

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

        valid_from = dateutil.parser.parse(element.get('valid_from'))
        valid_to = dateutil.parser.parse(element.get('valid_to'))

        # The file name is relative to the index file, so obtain an absolute path.
        file_name = element.text
        file_path = os.path.join(index_dir, file_name)
        
        try:
            cap = parse_cap_file(cap_schema, cap_file = file_path)
        except (ValueError, etree.XMLSyntaxError):
            sys.stderr.write("Error: CAP file '%s' is not valid.\n" % file_path)
            sys.exit(1)
        
        process_message(file_name, cap, messages, cancel, update)
    
    for reference_id, update_id in update.items():

        # If the identifier referred to by the Update message is in the index
        # then remove the corresponding Alert message before it is sent and
        # convert the Update message into an Alert, removing any references to
        # the original message. Remove the Update message from the update
        # dictionary.
        if reference_id in messages:
            sys.stdout.write("Updating message '%s' before it can be sent.\n" % reference_id)
            update_message(messages, reference_id, update_id)
            
            # Remove the original message from the message dictionary.
            del messages[reference_id]
            
            # Remove the Update message from the update dictionary.
            # The message itself is now an Alert message.
            del update[reference_id]
    
    for reference_id, cancel_id in cancel.items():

        # If the identifier referred to by the Cancel message is in the index
        # then remove the corresponding Alert message before it is sent.
        # Also remove the Cancel message from both the message and cancellation
        # dictionaries.
        if reference_id in messages:
            sys.stdout.write("Cancelling unpublished message '%s'.\n" % reference_id)

            # Remove the original message from the message dictionary.
            del messages[reference_id]

            # Remove the Cancel message from the message and cancellation dictionaries.
            del messages[cancel_id]
            del cancel[reference_id]
    
    return messages, cancel, update


def parse_rss_file(cap_schema, rss_file, output_dir):
    """Parses the given rss_file, returning message, cancellation and update
    dictionaries. The message dictionary contains messages in the order in which
    they appeared in the RSS file.
    
    Uses the cap_schema to validate CAP files that are read to obtain additional
    information that is not supplied in the RSS file.

    The message dictionary maps the identifier of each CAP file to the CAP
    document itself. The cancellation dictionary maps identifiers of
    messages that should be cancelled to the corresponding cancellation
    message identifiers."""

    try:
        rss = etree.parse(rss_file)
    except etree.XMLSyntaxError:
        sys.stderr.write("Error: RSS file '%s' is not valid.\n" % rss_file)
        sys.exit(1)
    
    # Create a dictionary mapping identifiers to tuples containing message types,
    # file names and CAP documents.
    messages = OrderedDict()
    # Create a dictionary mapping cancelled message identifiers to the identifiers
    # of the Cancel messages that refer to them, and a dictionary mapping updated
    # messages to the Update messages that refer to them.
    cancel = {}
    update = {}
    
    for element in rss.iterfind('.//item'):
    
        # Fetch the CAP file referred to by the RSS feed.
        url = element.find('.//link').text
        
        # If the file is mentioned in the RSS feed then it should still be
        # present locally.
        file_name = urlparse.urlparse(url).path.split('/')[-1]
        try:
            f = open(os.path.join(output_dir, file_name))
            cap_text = f.read()
            f.close()
        except IOError:
            sys.stderr.write("Error: failed to read CAP file '%s' previously published in RSS file '%s'.\n" % (file_name, rss_file))
            sys.exit(1)
        
        try:
            cap = parse_cap_file(cap_schema, cap_text = cap_text)
        except (ValueError, etree.XMLSyntaxError):
            sys.stderr.write("Warning: CAP file from URL '%s' is not valid.\n" % url)
            continue
        
        process_message(url, cap, messages, cancel, update)
    
    return messages, cancel, update


def main(index_file, rss_file, output_dir, base_url):
    """Controls the overall processing of CAP and index files to create an RSS feed.
    The given args are the arguments supplied by the user on the command line."""

    # Get the current time.
    now = datetime.datetime.now(dateutil.tz.tzutc())

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    if (os.path.exists("schemas")):
        schema_dirname = "schemas"
    else:
        schema_dirname = "/usr/share/xml/farekart"

    # Load the index schema.
    index_schema_doc = etree.parse(os.path.join(schema_dirname, "mifare-index.xsd"))
    index_schema = etree.XMLSchema(index_schema_doc)

    # Load the CAP schema.
    cap_schema_doc = etree.parse(os.path.join(schema_dirname, "CAP-v1.2.xsd"))
    cap_schema = etree.XMLSchema(cap_schema_doc)

    # Parse and validate the index file.
    messages, cancel, update = parse_index_file(index_schema, cap_schema, index_file)
    
    # Parse the RSS file, if found.
    if os.path.exists(rss_file):

        old_messages, old_cancel, old_update = parse_rss_file(cap_schema, rss_file, output_dir)
        
        # Merge the item dictionaries from the RSS and index files, keeping
        # any messages that have already been published.
        messages.update(old_messages)

        # Merge the cancellation dictionaries from the RSS and index files.
        # If there were duplicate cancellations then those messages will have
        # been discarded but the relationship between messages should still be
        # valid since it describes a single pair of existing messages.
        cancel.update(old_cancel)
        
        # Merge the update dictionaries from the RSS and index files.
        update.update(old_update)
    
    # At this point, we should only have new alerts, cancellations and updates
    # from the index and old alerts, cancellations and updates from the RSS file.
    
    # Check for expired messages and remove them, removing any cancellations
    # that refer to them. We cannot remove messages with cancellations that
    # are still valid since users may have only read the original messages.
    
    # Maintain a set of expired messages so that cancellations can also be expired.
    expired = set()
    new_messages = []

    for identifier in messages:
    
        try:
            msgType, file_name, cap = messages[identifier]
        except KeyError:
            continue

        if msgType == "Alert" or msgType == "Update":

            if expire_message(now, cap):

                # Expire the message (do not include it in the new list).
                sys.stdout.write("Expiring unpublished message '%s'.\n" % identifier)

                if identifier in cancel:
                    # Also expire the cancellation.
                    sys.stdout.write("Also expiring unpublished cancellation message '%s'.\n" % cancel[identifier])
                    expired.add(cancel[identifier])
            else:
                new_messages.append((file_name, cap))

        elif msgType == "Cancel":

            if identifier not in expired:
                new_messages.append((file_name, cap))
    
    # Write the unpublished CAP files to the output directory.
    # Note that we cannot just copy the files because some Update messages may
    # have been converted to Alert messages.
    index_dir = os.path.split(index_file)[0]
    
    for file_name, cap in new_messages:
    
        # Only published local files.
        if urlparse.urlparse(file_name).scheme == "":
            f = open(os.path.join(output_dir, file_name), 'wb')
            ElementTree(cap).write(f, encoding="UTF-8", xml_declaration=True, pretty_print=True)
            f.close()
    
    # Create a RSS feed.
    rss = Element('rss')
    rss.set('version', '2.0')
    
    channel = SubElement(rss, 'channel')
    SubElement(channel, 'title').text = "Weather alerts"
    SubElement(channel, 'link').text = base_url
    SubElement(channel, 'description').text = "Weather alerts from the Norwegian Meteorological Institute"
    SubElement(channel, 'lastBuildDate').text = now.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    for file_name, cap in new_messages:
    
        # Check if the file name is actually a URL.
        if urlparse.urlparse(file_name).scheme != "":
            # Use the URL supplied.
            url = file_name
        else:
            # Create the intended URL from the base URL and the file name.
            url = urlparse.urljoin(base_url, file_name)
        
        item = SubElement(channel, 'item')
        SubElement(item, 'title').text = cap.find('.//cap:headline', CAP_nsmap).text
        SubElement(item, 'link').text = url
        SubElement(item, 'description').text = cap.find('.//cap:description', CAP_nsmap).text
        SubElement(item, 'guid').text = cap.find('.//cap:identifier', CAP_nsmap).text
        SubElement(item, 'pubDate').text = cap.find('.//cap:sent', CAP_nsmap).text
        SubElement(item, 'author').text = cap.find('.//cap:sender', CAP_nsmap).text
        SubElement(item, 'category').text = cap.find('.//cap:category', CAP_nsmap).text
    
    # Write the new RSS feed file.
    f = open(rss_file, 'wb')
    ElementTree(rss).write(f, encoding='UTF-8', xml_declaration=True, pretty_print=True)
    f.close()
