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

"""Converts Common Alerting Protocol (CAP) files into KML files suitable for
use with Diana (http://diana.met.no)."""

import math, os, sys
import datetime, dateutil.parser
from lxml.etree import Element, ElementTree, SubElement
from lxml import etree

bdiana_template = """
buffersize=600x800
colour=COLOUR
filename=%(image file)s
output=PNG
setupfile=/etc/diana/setup/diana.setup-COMMON
settime=%(warning time)s

PLOT
MAP backcolour=white map=Gshhs-Auto contour=on cont.colour=black cont.linewidth=1 cont.linetype=solid cont.zorder=1 land=on land.colour=200:200:200 land.zorder=0 lon=off lat=off frame=off
AREA name=Norge
DRAWING file=%(kml file)s
LABEL data font=BITMAPFONT fontsize=8
LABEL text="$day $date $auto UTC" tcolour=red bcolour=black fcolour=white:200 polystyle=both halign=left valign=top font=BITMAPFONT fontsize=8
ENDPLOT
"""

def find_properties(element, names, nsmap):

    """Finds the subelements of the given element that correspond to properties
    with the specified names, using the namespace map, nsmap, to enable XPath
    searches with the cap: prefix."""

    properties = {}

    for name in names:
        p = element.find('.//cap:' + name, nsmap)
        if p is not None:
            properties[name] = p.text
    
    return properties

def write_extended_data_values(properties, extdata, prefix):

    """Writes the contents of the properties dictionary to the XML element,
    extdata, containing the extended data values, giving each piece of data
    the specified prefix string."""

    for key, value in properties.items():
        if type(value) == dict:
            write_extended_data_values(value, extdata, prefix + key + ":")
        else:
            data = SubElement(extdata, 'Data')
            data.set('name', prefix + key)
            SubElement(data, 'value').text = unicode(value)

if __name__ == "__main__":

    if not 2 <= len(sys.argv) <= 4:

        sys.stderr.write("Usage: %s <CAP file> [<KML file for Diana> [<input file for Diana>]]\n" % sys.argv[0])
        sys.exit(1)
    
    cap_file = sys.argv[1]
    
    if len(sys.argv) >= 3:
        kml_file = sys.argv[2]
    else:
        kml_file = None

    if len(sys.argv) == 4:
        input_file = sys.argv[3]
    else:
        input_file = None

    # Collect the starting times used in the CAP file.
    times = set()

    # Load the CAP schema.
    schema_doc = etree.parse(os.path.join("schemas", "CAP-v1.2.xsd"))
    schema = etree.XMLSchema(schema_doc)

    # Parse and validate the CAP file.
    root = etree.parse(cap_file)
    nsmap = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}

    if not schema.validate(root):
        sys.stderr.write("Error: CAP file '%s' is not valid.\n" % cap_file)
        sys.exit(1)

    # Obtain basic information about the alert.
    basic_info = find_properties(root, ['identifier', 'sender', 'sent',
        'status', 'msgType', 'scope'], nsmap)

    kml = Element('kml')
    kml.set('xmlns', "http://www.opengis.net/kml/2.2")
    doc = SubElement(kml, 'Document')
    
    # Obtain each info element in the file.
    for info in root.findall('.//cap:info', nsmap):

        # Create a folder for each info element in the KML file.

        folder = SubElement(doc, 'Folder')
        name = SubElement(folder, 'name')
        name.text = info.find('.//cap:event', nsmap).text

        optional_info = find_properties(info, ['headline', 'description'], nsmap)

        # Each info element may have effective and expires elements, but they
        # are optional.
        effective = info.find('.//cap:effective', nsmap)
        expires = info.find('.//cap:expires', nsmap)

        # We need either effective and expires properties or the time the
        # message was sent and the expires property.

        if expires is not None:

            if effective is not None:
                fromtime = dateutil.parser.parse(effective.text).strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                fromtime = dateutil.parser.parse(basic_info['sent']).strftime('%Y-%m-%dT%H:%M:%SZ')

            # Record the starting time for later use.
            times.add(fromtime)

            timespan = SubElement(folder, 'TimeSpan')
            begin = SubElement(timespan, 'begin')
            begin.text = fromtime
            end = SubElement(timespan, 'end')
            end.text = dateutil.parser.parse(expires.text).strftime('%Y-%m-%dT%H:%M:%SZ')

        # Compile a dictionary of properties for attributes in the info
        # element for inclusion in each Placemark.
        properties = find_properties(info, ['category', 'severity', 'urgency', 'certainty'], nsmap)
        properties['style:type'] = 'Dangerous weather warning'

        # Examine each area element in the info element.

        for area in info.findall('.//cap:area', nsmap):

            areaDesc = area.find('.//cap:areaDesc', nsmap)

            placemark = SubElement(folder, 'Placemark')
            SubElement(placemark, 'name').text = optional_info['headline']
            SubElement(placemark, 'description').text = areaDesc.text
            
            extdata = SubElement(placemark, 'ExtendedData')
            data = SubElement(extdata, 'Data')
            data.set('name', u'met:objectType')
            SubElement(data, 'value').text = 'PolyLine'
            
            # Add area-specific properties to the ones common to the info element.
            area_properties = find_properties(area, ['altitude', 'ceiling'], nsmap)
            geocode = area.find('.//cap:geocode', nsmap)
            if geocode is not None:
                area_properties['geocode:name'] = geocode.find('.//cap:valueName', nsmap).text
                area_properties['geocode:value'] = geocode.find('.//cap:value', nsmap).text

            area_properties.update(properties)

            # Write the info properties as extended data values.
            write_extended_data_values(area_properties, extdata, "met:info:cap:")

            # If the area contains a polygon then transfer its coordinates
            # to the KML file.
            polygon = area.find('.//cap:polygon', nsmap)

            if polygon is not None:

                kml_polygon = SubElement(placemark, 'Polygon')
                SubElement(kml_polygon, 'tessellate').text = '1'

                boundary = SubElement(kml_polygon, 'outerBoundaryIs')
                ring = SubElement(boundary, 'LinearRing')
                coordinates = SubElement(ring, 'coordinates')
                coordinates.text = ''

                # Coordinates are specified as latitude,longitude in CAP files
                # so we need to transpose them for KML. The first and last
                # points should already be the same.
                for coord in polygon.text.split():
                    if not coord:
                        continue
                    lat, lon = coord.split(',')
                    coordinates.text += lon + ',' + lat + '\n'

            # If the area contains a circle then transfer its coordinates
            # to the KML file as a polygon.
            circle = area.find('.//cap:circle', nsmap)

            if circle is not None:

                kml_polygon = SubElement(placemark, 'Polygon')
                SubElement(kml_polygon, 'tessellate').text = '1'

                boundary = SubElement(kml_polygon, 'outerBoundaryIs')
                ring = SubElement(boundary, 'LinearRing')
                coordinates = SubElement(ring, 'coordinates')
                coordinates.text = ''

                # Convert the circle with the given centre and radius to a
                # polygon with 20 points plus the first point again.
                centre, radius = circle.text.strip().split()
                clat, clon = map(float, centre.split(','))
                radius = float(radius)

                i = 0
                while i <= 20:
                    lat = clat + (radius * math.cos((i/20.0) * (math.pi/180)))
                    lon = clon + (radius * math.sin((i/20.0) * (math.pi/180)))
                    coordinates.text += '%f,%f\n' % (lon, lat)
                    i += 1
    
    if not kml_file:
        f = sys.stdout
    else:
        f = open(kml_file, 'wb')

    # Write the KML file.
    ElementTree(kml).write(f, encoding='UTF-8', xml_declaration=True, pretty_print=True)
    f.close()

    if input_file:

        stem = os.path.splitext(kml_file)[0]

        f = open(input_file, 'w')
        f.write("# Created by cap2kml.py at %s.\n" % datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'))

        # Create an input specification for bdiana and write it to a file.
        times = list(times)
        times.sort()
        i = 0

        for time in times:
            f.write(bdiana_template % {'image file': '%s-%i.png' % (stem, i),
                                       'warning time': time,
                                       'kml file': kml_file})
            i += 1

        f.close()

    sys.exit()
