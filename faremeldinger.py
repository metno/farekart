#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# Lese aktuelle kulingvarsler fra TED databasen og lage Produkt som kan vises i Diana.
#
# Author:
#  Bård Fjukstad.  Jan. 2015

"""Writes farevarsel (dangerous weather warning) products using data obtained
from a TED database.
"""

import sys
import MySQLdb
import time
import os

from fare_utilities import *
from generatecap_fare import *
from faremeldinger_v2 import *


def get_locations(db, select_string, time):
    """Retrieves all currently valid GALE forecasts from the TED database, db,
    using the given SQL select_string and time string."""

    try:
        cur = db.cursor()
        cur.execute(select_string, time)
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

        for n in locs.split(":"):

            latlon = get_latlon(n,db)
            if not latlon:
                continue

            name = latlon[0][0]
            placemark, coordinates = generate_placemark(document, name, value, df, dt)

            text = u''

            for name, lon, lat in latlon:
                line = u"%f,%f,0\n" % (lon, lat)
                text += line

            # Include the first point again to close the polygon.
            if latlon:
                name, lon, lat = latlon[0]
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

            latlon = get_latlon(n,db)
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

#
# MAIN
#
if __name__ == "__main__":

    if not 6 <= len(sys.argv) <= 7:
        sys.stderr.write("Usage: %s <TED db username> <passwd> <TEDDBhost> <TEDDB port> <directory for files> <Optional: OpenLayerDir>\n" % sys.argv[0])
        sys.exit(1)

    db = MySQLdb.connect(user=sys.argv[1],
                         passwd=sys.argv[2],
                         host=sys.argv[3],
                         port=int(sys.argv[4]),
                         db="ted")

    dirname = sys.argv[5]
    OpenLayer = False

    if len(sys.argv) == 7:
        ol_dirname = sys.argv[6]
        OpenLayer = True

    # Obtain a string containing the local time for the start of the current hour.
    now = time.strftime("%Y-%m-%d %H:%M:00")

### Gale Warnings

    select_string = 'select name,vfrom,vto,location,value from forecast where lang="EN" and vto > %s and name="MIkuling" order by vto desc'

    locations = get_locations(db, select_string, now)

    filename = os.path.join(dirname, "Current_gale.kml")

    generate_file(locations, db, filename, "Gale warning", "Label Gale")

    if OpenLayer:
        filename = os.path.join(ol_dirname, "Current_gale_ol.kml")
        generate_file_ol(locations,db, filename, "Gale warning", "Label Gale")

### OBS warnings

    select_string = 'select name,vfrom,vto,location,value from forecast where vto > %s and name in ("VA_Obsvarsel","VV_Obsvarsel","VN_Obsvarsel") order by vto desc'

    locations = get_locations(db, select_string, now)

    filename = os.path.join(dirname, "Current_obs.kml")

    generate_file(locations, db, filename, "Obs warning", "Label Obs")

    if OpenLayer:
        filename = os.path.join(ol_dirname, "Current_obs_ol.kml")
        generate_file_ol(locations,db, filename, "Obs warning", "Label Obs")

### Extreme forecasts

    select_string='select name,vfrom,vto,location,value from forecast where vto > %s and name in ("MIekstrem_FaseA","MIekstrem") order by vto desc'

    locations = get_locations(db, select_string, now)

    filename = os.path.join(dirname, "Current_extreme.kml")

    generate_file(locations, db, filename, "Extreme forecast", "Label Extreme")

    if OpenLayer:
        filename = os.path.join(ol_dirname, "Current_extreme_ol.kml")
        generate_file_ol(locations, db, filename, "Extreme forecast", "Label Extreme")

### Farevarsler

    select_string='select value,termin from document where name = "MIfare" and vto > %s'

    filename = os.path.join(dirname, "Current_fare.kml")

    generate_file_fare(db, filename, "Dangerous weather warning", "Label Faremelding", now, select_string)

    filebase = os.path.join(dirname, "MIfare")

    generate_files_cap_fare(select_string, now, db, filebase)

### Farevarsler TEST

    select_string='select value from document where name = "x_test_MIfare" and vto > %s'

    filename = os.path.join(dirname, "Current_fare_test.kml")

    generate_file_fare( db, filename, "Dangerous weather warning", "Label Faremelding", now, select_string )


## Close

    if db:
        db.close()
