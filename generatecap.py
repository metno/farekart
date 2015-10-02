#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# Bruke aktuelle farevarsler fra TED databasen og lage CAP melding
#
# Kilde til CAP : http://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.pdf
#
#
# Author:
#  Bård Fjukstad.  Jan. 2015
#

"""Generates Common Alerting Protocol (CAP) files for farevarsel (dangerous
weather warning) reports obtained from a TED database.
"""

import codecs, os, sys, time, uuid
from lxml.etree import Element, SubElement, tostring
from fare_common import get_latlon


def generate_file_cap(locations, db, filename, type):
    """Writes the given locations to a CAP file.

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

    numAreas = 0

    now = time.strftime("%Y-%m-%dT%H:00:00-00:00")
    name = "%s warnings at %s" % ( type, now )
    randomIdentifier = uuid.uuid4()

    alert = Element('alert')
    alert.set('xmlns', "urn:oasis:names:tc:emergency:cap:1.2")

    SubElement(alert, 'identifier').text = randomIdentifier
    SubElement(alert, 'sender').text = "helpdesk@met.no"
    SubElement(alert, 'sent').text = now
    SubElement(alert, 'status').text = 'Actual'
    SubElement(alert, 'msgType').text = 'Alert'
    SubElement(alert, 'scope').text = 'Public'

    # Optional element
    SubElement(alert, 'note').text = u'%s alert for %s issued by the Norwegian Meteorological Institute' % (type, 'Norway')

    for varsel in locations:

        vname = varsel[0]
        dateto = varsel[2]
        locs = varsel[3]

        # Text in the TED database is in ISO 8859-1 encoding.
        desc = varsel[4].decode("iso8859-1")

        info = SubElement(alert, 'info')
        SubElement(info, 'category').text = 'Met'
        SubElement(info, 'event').text = type
        SubElement(info, 'urgency').text = 'Expected'
        SubElement(info, 'severity').text = 'Moderate'
        SubElement(info, 'certainty').text = 'Likely'

        # Optional elements
        SubElement(info, 'effective').text = now
        SubElement(info, 'expires').text = dateto.strftime("%Y-%m-%dT%H:%M:00-00:00")

        for n in locs.split(":"):

            latlon = get_latlon(n, db)
            if not latlon:
                continue

            name = latlon[0][0]

            area = SubElement(info, 'area')
            SubElement(area, 'areaDesc').text = name

            if len(latlon) < 3:
                continue

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

        numAreas += 1

    # If no areas found, return without writing the file.
    if numAreas == 0:
        return

    f = open(filename, 'w')
    f.write(tostring(alert, encoding="UTF-8", xml_declaration=True, pretty_print=True, standalone=True))
    f.close()
