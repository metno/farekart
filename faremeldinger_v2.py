#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# Lese aktuelle Farevarsler fra TED databasen og lage Produkt som kan vises i Diana.
#
# Author:
# Bård Fjukstad.  Mar. 2015

"""Writes farevarsel (dangerous weather warning) products using data obtained
from a TED database.
"""

import codecs
import sys
import MySQLdb
import time
import os
from lxml.etree import Element, SubElement, tostring

from fare_utilities import *
from generatecap import *


def get_xml_docs(db, dateto, select_string):
    """Retrieves a full set of documents from the database, db, using the given
    SQL select_string. The end of the period for which forecasts are obtained
    is given by the dateto string."""

    try:
        cur = db.cursor()
        cur.execute(select_string, dateto)
        result = cur.fetchall()

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        return None

    return result


def retrieve_from_xml_fare(xmldoc):
    """Retrieves some parameters from the XML text for a faremelding specified
    by xmldoc and returns them as a list of values."""

    vto = None
    vfrom = None
    locations = {}
    res={}
    n = 0

    # print xmldoc

    root = ET.fromstring(xmldoc)

    vto = None
    vfrom = None
    ty = None
    sender = None
    type = None
    id = None
    mnr = None
    eventname = None

    for t in root.iter('time'):
        # print "Tag: ",t.tag, " Attrib: ", t.attrib

        vto = t.get('vto')
        vfrom = t.get('vfrom')

        for keyword in t.iter('keyword'):

            nam = keyword.get('name')

            if nam == "type":
                type = keyword.find('in').text
            elif nam == "mnr":
                mnr = keyword.find('in').text
            elif nam == "sender":
                sender = keyword.find('in').text
            elif nam == "navn":
                eventname = keyword.find('in').text

        for header in root.iter('productheader'):
            id = header.find('dockey').text

        for p in root.iter('productdescription'):
            termin = p.get('termin')

    # Foreach time, Ony one in each time.
    for location in root.iter('location'):

        name = None
        varsel = None
        nam = None
        severity = None
        certainty = None
        trigglevel = None
        english = None
        kommentar = None
        pictlink = None
        retperiode = None
        consequence = None
        infolink = None

        loc = {}

        l_id = location.get('id')
        l_name = location.find('header').text

        for param in location.findall('parameter'):

            nam = param.get('name')

            if nam == "varsel":
                varsel = param.find('in').text
            elif nam == "severity":
                severity = param.find('in').text
            elif nam == "certainty":
                certainty = param.find('in').text
            elif nam == "picturelink":
                pictlink = param.find('in').text
            elif nam == "returnperiod":
                retperiode = param.find('in').text
            elif nam == "consequence":
                consequence = param.find('in').text
            elif nam == "infolink":
                infolink = param.find('in').text
            elif nam == "triggerlevel":
                trigglevel = param.find('in').text
            elif nam == "englishforecast":
                english = param.find('in').text
            elif nam == "coment":
                kommentar = param.find('in').text

        loc['name'] = l_name
        loc['id'] = l_id
        loc['type'] = ty
        loc['varsel'] = varsel
        loc['severity'] = severity
        loc['certainty'] = certainty
        loc['pictlink'] = pictlink
        loc['infolink'] = infolink
        loc['retperiode'] = retperiode
        loc['consequence'] = consequence
        loc['kommentar'] = kommentar
        loc['triggerlevel'] = trigglevel
        loc['english'] = english

        n = n + 1

        locations[n] = loc

    res['locations'] = locations
    res['vfrom'] = vfrom
    res['vto'] = vto
    res['termin'] = termin
    res['eventname'] = eventname
    res['sender'] = sender
    res['type'] = type
    res['id'] = id
    res['mnr'] = mnr

    return res


def retrieve_from_xml(value):
    """Retrieves some parameters from the XML text specified by xmldoc and
    returns them as a list of values."""

    results = {}
    i = 0

    for doc in value:

        vto = None
        vfrom = None
        locations = {}
        res = {}

        n = 0

        xmldoc = doc[0]

        # print xmldoc

        root = ET.fromstring(xmldoc)

        vto = None
        vfrom = None
        ty = None
        sender = None
        type = None
        id = None
        mnr = None
        eventname = None

        for t in root.iter('time'):
            # print "Tag: ",t.tag, " Attrib: ", t.attrib

            vto = t.get('vto')
            vfrom = t.get('vfrom')

            for keyword in t.iter('keyword'):

                nam = keyword.get('name')

                if nam == "type":
                    type = keyword.find('in').text
                elif nam == "mnr":
                    mnr = keyword.find('in').text
                elif nam == "sender":
                    sender = keyword.find('in').text
                elif nam == "navn":
                    eventname = keyword.find('in').text

            for header in root.iter('productheader'):
                id = header.find('dockey').text

            for p in root.iter('productdescription'):
                termin = p.get('termin')

        # Foreach time, Ony one in each time.
        for location in root.iter('location'):

            name = None
            varsel = None
            nam = None
            severity = None
            certainty = None
            trigglevel = None
            english = None
            kommentar = None
            pictlink = None
            retperiode = None
            consequence = None
            infolink = None

            loc = {}

            l_id = location.get('id')
            l_name = location.find('header').text

            for param in location.findall('parameter'):

                nam = param.get('name')

                if nam == "varsel":
                    varsel = param.find('in').text
                elif nam == "severity":
                    severity = param.find('in').text
                elif nam == "certainty":
                    certainty = param.find('in').text
                elif nam == "picturelink":
                    pictlink = param.find('in').text
                elif nam == "returnperiod":
                    retperiode = param.find('in').text
                elif nam == "consequence":
                    consequence = param.find('in').text
                elif nam == "infolink":
                    infolink = param.find('in').text
                elif nam == "triggerlevel":
                    trigglevel = param.find('in').text
                elif nam == "englishforecast":
                    english = param.find('in').text
                elif nam == "coment":
                    kommentar = param.find('in').text

            loc['name'] = l_name
            loc['id'] = l_id
            loc['type'] = ty
            loc['varsel'] = varsel
            loc['severity'] = severity
            loc['certainty'] = certainty
            loc['pictlink'] = pictlink
            loc['infolink'] = infolink
            loc['retperiode'] = retperiode
            loc['consequence'] = consequence
            loc['kommentar'] = kommentar
            loc['triggerlevel'] = trigglevel
            loc['english'] = english

            n = n + 1

            locations[n] = loc

        res['locations'] = locations
        res['vfrom'] = vfrom
        res['vto'] = vto
        res['termin'] = termin
        res['eventname'] = eventname
        res['sender'] = sender
        res['type'] = type
        res['id'] = id
        res['mnr'] = mnr

        results[i] = res
        i = i + 1

    return results


def generate_file_fare(db, filename, type, labelType, dateto, select_string):
    """Obtains warnings from the database, db, and writes a KML file with the
    given filename. The warnings are selected for the period ending with the
    data, dateto, using the given SQL select_string.

    The strings passed as arguments to the type and labelType parameters are
    unused."""

    kml = Element('kml')
    kml.set('xmlns', "http://www.opengis.net/kml/2.2")
    document = SubElement(kml, 'Document')

    doc = get_xml_docs(db, dateto, select_string)
    results = retrieve_from_xml(doc)

    for i in results:

        res = results[i]

        dt = time.strptime(res['vto'], "%Y-%m-%d %H:%M:%S")
        dt = time.strftime("%Y-%m-%dT%H:%M:00Z", dt)

        df = time.strptime(res['vfrom'], "%Y-%m-%d %H:%M:%S")
        df = time.strftime("%Y-%m-%dT%H:%M:00Z", df)

        for p in res['locations']:

            locs = res['locations'][p]

            for n in locs['id'].split(":"):

                latlon = get_latlon(n, db)
                first = 0
                value = locs['varsel']
                comm = locs['kommentar']
                sev = locs['severity']

                ty = locs['type']
                cer = locs['certainty']
                tri = locs['triggerlevel']
                eng = locs['english']

                placemark = SubElement(document, 'Placemark')
                SubElement(placemark, 'name').text = name
                SubElement(placemark, 'description').text = value

                timespan = SubElement(placemark, 'TimeSpan')
                begin = SubElement(timespan, 'begin')
                begin.text = df
                end = SubElement(timespan, 'end')
                end.text = dt

                extdata = SubElement(placemark, 'ExtendedData')

                # Convert the properties associated with this polygon into
                # extended data values.
                properties = [
                    ("met:objectType",          "PolyLine"),
                    ("met:style:type",          "Dangerous weather warning"),
                    ("met:info:type",           locs['type']),
                    ("met:style:fillcolour",    locs['severity']),
                    ("met:info:severity",       locs['severity']),
                    ("met:info:comment",        locs['kommentar']),
                    ("met:info:Certainty",      locs['certainty']),
                    ("met:info:Triggerlevel",   locs['triggerlevel']),
                    ("met:info:English",        locs['english'])
                    ]

                for key, value in properties:
                    data = SubElement(extdata, 'Data')
                    data.set('name', key)
                    SubElement(data, 'value').text = value

                polygon = SubElement(placemark, 'Polygon')
                SubElement(polygon, 'tessellate').text = '1'

                boundary = SubElement(polygon, 'outerBoundaryIs')
                ring = SubElement(boundary, 'LinearRing')
                coordinates = SubElement(ring, 'coordinates')

                text = u''

                for name, lon, lat in latlon:
                    line = u"%f,%f,0\n" % (lon, lat)
                    text += line

                coordinates.text = text

    f = open(filename, 'w')
    f.write(tostring(kml, encoding="UTF-8", xml_declaration=True, pretty_print=True))
    f.close()
