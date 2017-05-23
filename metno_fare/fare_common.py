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

import codecs, difflib, os, sys, time
from lxml.etree import Element, SubElement, fromstring, tostring
import MySQLdb


def get_xml_docs(db, dateto, select_string):
    """Retrieves a full set of documents from the database, db, using the given
    SQL select_string. The end of the period for which forecasts are obtained
    is given by the dateto string."""

    try:
        cur = db.cursor()
        cur.execute(select_string, (dateto,))
        result = cur.fetchall()

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        return None

    return result

def translate_name(db,lang,name):
    translated_name=name
    if (lang=="en-GB"):
        select_string = "select english from phrase4 where bokmal = %s"
        try:
            cur = db.cursor()
            cur.execute(select_string, (name,))
            result = cur.fetchone()
            if result and result[0]:
                translated_name = result[0].decode("iso8859-1")

        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])

    return translated_name


def get_latlon(n, db):
    """Retrieves the Geographical corners for the given TED defined area ID, n,
    from the database, db."""

    select_string = "select name, corners from location where id = %s"

    try:
        cur = db.cursor()
        cur.execute(select_string, (n,))
        result = cur.fetchone()

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])

    retval = []

    # Names are ISO 8859-1 encoded in the TED database.
    if not result:
        return ("",retval)

    name = result[0].decode("iso8859-1")

    #print("name",name)

    if not (":" in result[1]):
        return (name,retval)

    for n in result[1].split(":"):

        o,p = n.split(" ")


        lo = int(o) / 10000.0
        la = int(p) / 10000.0

        lon = int(lo) + ( (lo - int(lo) )*100.0/60.0 )

        lat = int(la) + ( (la - int(la) )*100.0/60.0 )

        retval.append((lon,lat))

    return (name,retval)


def retrieve_from_xml_fare(xmldoc):
    """Retrieves some parameters from the XML text for a faremelding specified
    by xmldoc and returns them as a list of values."""

    locations = []
    res={}

    root = fromstring(xmldoc)

    sender = None #dangerwarning spesific
    id = "BLANK" #dangerwarning spes# ific
    mnr = None #dangerwarning spesific
    alert = None #dangerwarning spesific

    t = root.find('dangerwarning')
	# new types of warnings using metfare template and <dangerwarning> tag.

    if t is not None and len(t) > 1:
      alert = t.find('msgtype').text # all this stuff is common to the whole CAP-file
      mnr   = t.find('msgnumber').text
      references = t.find('msgreferences').text
      sender = t.find('msgauthor').text
      id = t.find('msgidentifier').text

    header = root.find('productheader')
    if header is not None:
        res['phenomenon_type'] = header.findtext('phenomenon_type')
        res['phenomenon_name'] = header.findtext('phenomenon_name')
        res['phenomenon_number'] = header.findtext('phenomenon_number')

    p = root.find('productdescription')
    if p is not None:
        termin = p.get('termin')



    for time in root.iter('time'):

        vto = time.get('vto')
        vfrom = time.get('vfrom')

        for f in time.iter('forecasttype'):
            forecasttype= f.get('name')

            for location in f.iter('location'):
                #print(forecasttype)
                res['forecasttype']=forecasttype
                loc = {}

                loc['id'] = location.get('id')
                loc['name'] = location.find('header').text
                loc['effective'] = termin

                for param in location.findall('parameter'):
                    nam = param.get('name')
                    temp = param.find('in')
                    value = "\n".join(temp.itertext())
                    loc[nam]=value

                loc['vfrom']=vfrom
                loc['vto']=vto

                locations.append(loc)

    res['locations'] = locations
    res['termin'] = termin
    res['sender'] = sender
    res['id'] = id
    res['mnr'] = mnr
    res['alert'] = alert
    res['references']= references
    return res # res is all the info just obtained from the Ted document

def retrieve_from_xml(value):
    """Retrieves parameters from MULTIPLE files returned"""

    results = {}
    i = 0

    for doc in value:

        xmldoc = doc[0]

        res = retrieve_from_xml_fare(xmldoc)

        results[i] = res
        i = i + 1
            
    return results

def get_locations(db, select_string, time):
    """Retrieves all currently valid GALE forecasts from the TED database, db,
    using the given SQL select_string and time string."""

    try:
        cur = db.cursor()
        cur.execute(select_string, (time,))
        result = cur.fetchall()

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])

    return result


def generate_placemark(parent, name, value, df, dt):

    placemark = SubElement(parent, 'Placemark')
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
        ("met:style:type",          "Gale warning"),
        ("met:info:type",           "Gale warning"),
        ("met:style:fillcolour",    "yellow"),
        ("met:style:fillalpha",     "128"),
        ("met:info:severity",       "yellow")
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

    return placemark, coordinates


def generate_file(locations, db, filename, type, labelType):
    """Writes the given locations to a file with the given filename, first as
    AREAS then as LABELs, using the database, db, to obtain latitude and
    longitude information for each location.
    The strings specifying the warning type and the labelType are currently
    unused."""

    kml = Element('kml')
    kml.set('xmlns', "http://www.opengis.net/kml/2.2")
    document = SubElement(kml, 'Document')

    for n in range(len(locations)):

        varsel = locations[n]
        vname = varsel[0]
        datefrom = varsel[1]
        dateto = varsel[2]
        locs = varsel[3]
        # Text is encoded as ISO 8859-1 in the TED database.
        value = varsel[4].decode("iso8859-1")

        # Strip tags from TED output.
        for tag in "<in>", "</in>":
            value = value.replace(tag, "")

        dt = dateto.strftime("%Y-%m-%dT%H:%M:00Z")
        df = datefrom.strftime("%Y-%m-%dT%H:%M:00Z")

        for id in locs.split(":"):

            name, latlon = get_latlon(id,db)
            if not latlon:
                continue

            placemark, coordinates = generate_placemark(document, name, value, df, dt)

            text = u''

            for lon, lat in latlon:
                line = u"%f,%f,0\n" % (lon, lat)
                text += line

            # Include the first point again to close the polygon.
            if latlon:
                lon, lat = latlon[0]
                text += u"%f,%f,0\n" % (lon, lat)

            coordinates.text = text

    f = open(filename, 'w')
    f.write(tostring(kml, encoding="UTF-8", xml_declaration=True, pretty_print=True))
    f.close()


def generate_file_ol(locations, db, filename, type, labelType):
    """Version for OpenLayers use.
    Writes the given locations to a file with the given filename, first as
    AREAS then as LABELs, using the database, db, to obtain latitude and
    longitude information for each location.
    The string specifying the warning type is included in the information for
    each location.
    The labelType string is currently unused."""

    kml = Element('kml')
    kml.set('xmlns', "http://www.opengis.net/kml/2.2")
    document = SubElement(kml, 'Document')

    symbols = []

    now = time.strftime("%Y-%m-%d %H:00")

    name = "%s warnings at %s" % ( type, now )

    for n in range(len(locations)):

        varsel = locations[n]
        vname = varsel[0]
        datefrom = varsel[1]
        dateto = varsel[2]
        locs = varsel[3]
        # Text is encoded as ISO 8859-1 in the TED database.
        value = varsel[4].decode("iso8859-1")

        # Strip tags from TED output.
        for tag in "<in>", "</in>":
            value = value.replace(tag, "")

        dt = dateto.strftime("%Y-%m-%dT%H:%M:00Z")
        df = datefrom.strftime("%Y-%m-%dT%H:%M:00Z")

        for n in locs.split(":"):

            name, latlon = get_latlon(n,db)
            if not latlon:
                continue

            name = latlon[0][0]

            # Add a placemark for each location.
            placemark, coordinates = generate_placemark(document, name, value, df, dt)

            lattop = 0
            latbot = 90
            lontop = 0
            lonbot = 180
            text = u''

            for name, lon, lat in latlon:

                if lat > lattop: lattop = lat
                if lat < latbot: latbot = lat
                if lon > lontop: lontop = lon
                if lon < lonbot: lonbot = lon

                line = u"%f,%f,0\n" % (lon, lat)
                text += line

            # Include the first point again to close the polygon.
            if latlon:
                name, lon, lat = latlon[0]
                text += u"%f,%f,0\n" % (lon, lat)

            coordinates.text = text

            slat = latbot + (lattop - latbot )/2.0
            slon = lonbot + (lontop - lonbot )/2.0

            symbols.append((vname, name + " " + value + " " + str(dateto), dateto, slat, slon))

    # Add a placemark for each symbol.

    for sentral, omrade, tidto, slat, slon in symbols:

        placemark = SubElement(document, "Placemark")
        SubElement(placemark, 'name').text = omrade + " " + tidto.strftime("%Y-%m-%d %H:%M")

        point = SubElement(placemark, "Point")
        coordinates = SubElement(point, "coordinates")
        coordinates.text = u"%f,%f,0" % (float(slon), float(slat))

    f = open(filename, 'w')
    f.write(tostring(kml, encoding="UTF-8", xml_declaration=True, pretty_print=True))
    f.close()


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

        for locs in res['locations']:

            dt = time.strptime(locs['vto'], "%Y-%m-%d %H:%M:%S")
            dt = time.strftime("%Y-%m-%dT%H:%M:00Z", dt)

            df = time.strptime(locs['vfrom'], "%Y-%m-%d %H:%M:%S")
            df = time.strftime("%Y-%m-%dT%H:%M:00Z", df)

            name, latlon = get_latlon(locs['id'], db)
            placemark = SubElement(document, 'Placemark')
            SubElement(placemark, 'name').text = locs['name']
            SubElement(placemark, 'description').text = locs['varsel']

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
                ("met:info:type",           locs.get('phenomenon_type')),
                ("met:style:fillcolour",    locs['severity']),
                ("met:info:severity",       locs['severity']),
                ("met:info:comment",        locs.get('coment')),
                ("met:info:Certainty",      locs['certainty']),
                ("met:info:Triggerlevel",   locs['triggerlevel']),
                ("met:info:English",        locs.get('englishforecast'))
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

            for lon, lat in latlon:
                line = u"%f,%f,0\n" % (lon, lat)
                text += line

            coordinates.text = text

    f = open(filename, 'w')
    f.write(tostring(kml, encoding="UTF-8", xml_declaration=True, pretty_print=True))
    f.close()
