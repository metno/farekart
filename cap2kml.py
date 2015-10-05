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

import os, sys
import dateutil.parser
from lxml.etree import Element, ElementTree, SubElement
from lxml import etree

def find_properties(element, names, nsmap):

    properties = {}

    for name in names:
        p = element.find('.//cap:' + name, nsmap)
        if p is not None:
            properties[name] = p.text
    
    return properties

def write_extended_data_values(properties, extdata, prefix):

    for key, value in properties.items():
        if type(value) == dict:
            write_extended_data_values(value, extdata, prefix + key + ":")
        else:
            data = SubElement(extdata, 'Data')
            data.set('name', prefix + key)
            SubElement(data, 'value').text = unicode(value)

if __name__ == "__main__":

    if not 2 <= len(sys.argv) <= 3:

        sys.stderr.write("Usage: %s <CAP file> [KML file for Diana]\n" % sys.argv[0])
        sys.exit(1)
    
    cap_file = sys.argv[1]
    
    if len(sys.argv) == 3:
        kml_file = sys.argv[2]
    else:
        kml_file = None

    # Load the CAP schema.
    schema_doc = etree.parse(os.path.join("schemas", "CAP-v1.2.xsd"))
    schema = etree.XMLSchema(schema_doc)

    # Parse and validate the CAP file.
    root = etree.parse(cap_file)
    nsmap = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}

    if not schema.validate(root):
        sys.stderr.write("Error: CAP file '%s' is not valid.\n" % cap_file)
        sys.exit(1)

    kml = Element('kml')
    kml.set('xmlns', "http://www.opengis.net/kml/2.2")
    doc = SubElement(kml, 'Document')
    
    # Obtain each info element in the file.
    for info in root.findall('.//cap:info', nsmap):

        # Create a folder for each info element in the KML file.

        folder = SubElement(doc, 'Folder')
        name = SubElement(folder, 'name')
        name.text = info.find('.//cap:event', nsmap).text

        desc = info.find('.//cap:description', nsmap)
        if desc is not None:
            description = desc.text
        else:
            description = ''

        # Each info element may have effective and expires elements, but they
        # are optional.
        effective = info.find('.//cap:effective', nsmap)
        expires = info.find('.//cap:expires', nsmap)

        if effective is not None and expires is not None:
            timespan = SubElement(folder, 'TimeSpan')
            begin = SubElement(timespan, 'begin')
            begin.text = dateutil.parser.parse(effective.text).strftime('%Y-%m-%dT%H:%M:%SZ')
            end = SubElement(timespan, 'end')
            end.text = dateutil.parser.parse(expires.text).strftime('%Y-%m-%dT%H:%M:%SZ')

        # Compile a dictionary of properties for attributes in the info
        # element for inclusion in each Placemark.
        properties = find_properties(info, ['category', 'severity', 'urgency', 'certainty'], nsmap)

        # Examine each area element in the info element.

        for area in info.findall('.//cap:area', nsmap):

            areaDesc = area.find('.//cap:areaDesc', nsmap)

            placemark = SubElement(folder, 'Placemark')
            SubElement(placemark, 'name').text = areaDesc.text
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
                coordinates.text = polygon.text
    
    if not kml_file:
        f = sys.stdout
    else:
        f = open(kml_file, 'wb')
    
    ElementTree(kml).write(f, encoding='UTF-8', xml_declaration=True, pretty_print=True)
    sys.exit()
