#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# Bruke aktuelle farevarsler fra TED databasen og lage CAP melding
#
# Kilde til CAP : http://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.pdf
#
#
# Author:
# Bård Fjukstad.  Jan. 2015
#

"""Generates Common Alerting Protocol (CAP) files for farevarsel (dangerous
weather warning) reports obtained from a TED database.
"""

import glob, os, sys, uuid
from datetime import datetime

from lxml.etree import Element, SubElement, tostring

from fare_utilities import get_latlon
from faremeldinger_v2 import *


def make_list_of_valid_files(filebase):

    files = []
    filesearch = "{0}*.cap".format(filebase)
    filenames = glob.glob(filesearch)

    for fname in filenames:
        print(fname)
        file = open(fname, 'r')
        xmldoc = file.read()
        root = fromstring(xmldoc)
        attributes = {}
        for info in root.iter('{urn:oasis:names:tc:emergency:cap:1.2}info'):
            valid_from = time.strptime(info.find('{urn:oasis:names:tc:emergency:cap:1.2}effective').text, "%Y-%m-%dT%H:%M:%S+00:00")
            valid_to = time.strptime(info.find('{urn:oasis:names:tc:emergency:cap:1.2}expires').text, "%Y-%m-%dT%H:%M:%S+00:00")
            attributes["valid_from"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", valid_from)
            attributes["valid_to"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", valid_to)
        file = [fname, attributes]
        #TODO- check if file is valid before appending
        files.append(file)


    # produce the xml-file

    root = Element('files', nsmap = {'xsi': "http://www.w3.org/2001/XMLSchema-instance"})
    root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation", "mifare-index.xsd")

    for filename, valid in files:
        child = SubElement(root, 'file', valid)
        child.text = os.path.split(filename)[1]

    listfilename="{0}-index.xml".format(filebase)
    listfile = open(listfilename, "w")
    listfile.write(tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True))
    listfile.close()




def get_urgency(date_from, now):
    """Finds the urgency based on the valid from date, date_from, and the
    current date, now."""

    dif = date_from - now

    if dif.total_seconds() < 0:
        return "Immediate"
    if dif.total_seconds() < 3600:
        return "Expected"

    return "Future"


def generate_file_cap_fare(filename, xmldoc, db):
    """Obtains the locations from the XML document given by xmldoc and the
    database, db, and writes a CAP file with the given filename.

    Structure:

        ALERT
            |
            | ---- One or more --  INFO
            |                        |
            |                        | -- one or more -- RESOURCE
            |                        |
            |                        | -- one or more -- AREA
            |                        |
            |                    end INFO
            |
        end ALERT"""

    res = retrieve_from_xml_fare(xmldoc)
    numAreas = 0
    sender = res['sender']
    eventname = res['eventname']
    l_type = res['type']
    mnr = res['mnr']

    now = datetime.now()
    name = "%s at %s" % (type, now.strftime("%Y-%m-%dT%H:00:00+00:00"))
    identifier = res['id']

    alert = Element('alert')
    alert.set('xmlns', "urn:oasis:names:tc:emergency:cap:1.2")

    SubElement(alert, 'identifier').text = identifier
    SubElement(alert, 'sender').text = "helpdesk@met.no"
    SubElement(alert, 'sent').text = now.strftime("%Y-%m-%dT%H:00:00+00:00")
    SubElement(alert, 'status').text = 'Actual'
    SubElement(alert, 'msgType').text = 'Alert'
    SubElement(alert, 'scope').text = 'Public'

    # Optional element
    SubElement(alert, 'note').text = u'%s alert for %s issued by the Norwegian Meteorological Institute' % (l_type, 'Norway')

    dt = datetime.strptime(res['vto'], "%Y-%m-%d %H:%M:%S")
    df = datetime.strptime(res['vfrom'], "%Y-%m-%d %H:%M:%S")

    urgency = get_urgency(dt, now)

    for p in res['locations']:

        locs = res['locations'][p]

        # Although the CAP format allows multiple areas per info element,
        # we only include one in each element.

        for n in locs['id'].split(":"):

            comm = locs['kommentar']
            tri = locs['triggerlevel']
            eng = locs['english']
            pict = locs['pictlink']
            infolink = locs['infolink']

            info = SubElement(alert, 'info')
            SubElement(info, 'language').text = 'no'
            SubElement(info, 'category').text = 'Met'
            SubElement(info, 'event').text = locs['type']
            SubElement(info, 'urgency').text = urgency
            SubElement(info, 'severity').text = locs['severity']
            SubElement(info, 'certainty').text = locs['certainty']

            # Write UTC times to the CAP file.
            SubElement(info, 'effective').text = df.strftime("%Y-%m-%dT%H:%M:00+00:00")
            SubElement(info, 'expires').text = dt.strftime("%Y-%m-%dT%H:%M:00+00:00")

            SubElement(info, 'senderName').text = sender
            SubElement(info, 'description').text = locs['varsel']
            SubElement(info, 'instruction').text = locs['consequence']
            SubElement(info, 'web').text = 'http://www.yr.no'

            if pict:
                resource = SubElement(info, 'resource')
                SubElement(resource, 'resourceDesc').text = "Grafiske beskrivelse av farevarslet"
                SubElement(resource, 'mimeType').text = "image/png"
                SubElement(resource, 'uri').text = pict

            if infolink:
                resource = SubElement(info, 'resource')
                SubElement(resource, 'resourceDesc').text = "Tilleggsinformasjon tilgjengelig fra andre"
                SubElement(resource, 'mimeType').text = "text/html"
                SubElement(resource, 'uri').text = infolink

            area = SubElement(info, 'area')
            SubElement(area, 'areaDesc').text = locs['name']

            latlon = get_latlon(n, db)
            if len(latlon) >= 3:

                # Optional polygon element with three unique points and the last
                # point identical to the first to close the polygon (at least
                # four points in total).
                polygon = SubElement(area, 'polygon')

                text = u''

                for name, lon, lat in latlon:
                    line = u"%f,%f\n" % (lon, lat)
                    text += line

                # Include the first point again to close the polygon.
                if latlon:
                    name, lon, lat = latlon[0]
                    text += u"%f,%f\n" % (lon, lat)

                polygon.text = text

                geocode = SubElement(area, 'geocode')
                SubElement(geocode, 'valueName').text = 'TED'
                SubElement(geocode, 'value').text = locs['id']

        numAreas += 1

    # If no areas found, return without writing the file.
    if numAreas == 0:
        return

    f = open(filename, 'w')
    f.write(tostring(alert, encoding="UTF-8", xml_declaration=True, pretty_print=True, standalone=True))
    f.close()


def generate_files_cap_fare(selectString, dateto, db, filebase):
    """Generates CAP files for the warnings obtained from the database, db,
    using the given selectString and dateto string.
    """

    docs = get_xml_docs(db, dateto, selectString)
    for doc in docs:

        tt=doc[1]
        tt = tt.strftime("%Y%m%dT%H%M00")
        filename = filebase + "-" + tt + ".cap"
        if (os.path.isfile(filename)):
            print "File already exists!"
        else:
            xmldoc=doc[0]
            generate_file_cap_fare(filename, xmldoc, db)

    make_list_of_valid_files(filebase)
