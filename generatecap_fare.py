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
import codecs
import sys
import uuid
from datetime import datetime
import os

from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, Comment, tostring, fromstring
import glob


from fare_utilities import *
from faremeldinger_v2 import *

CAP_HEADING = """<?xml version = '1.0' encoding = 'UTF-8' standalone = 'yes'?>

"""

CAP_ALERT = """
<cap:alert xmlns:cap="urn:oasis:names:tc:emergency:cap:1.2"> 

<!-- Mandatory elements -->
<cap:identifier>%s</cap:identifier> 
<cap:sender>%s</cap:sender>
<cap:sent>%s</cap:sent>
<cap:status>Actual</cap:status>
<cap:msgType>Alert</cap:msgType>
<cap:scope>Public</cap:scope>

<cap:note>%s alert for %s issued by the Norwegian Meteorological Institute</cap:note>

"""
#Cap_alert needs : Identifier, sender, sent-datetime, note-type, note-areaname

CAP_INFO = """
<cap:info>

<cap:language>no</cap:language>
<cap:category>Met</cap:category>
<cap:event>%s</cap:event>
<cap:urgency>%s</cap:urgency>
<cap:severity>%s</cap:severity>
<cap:certainty>%s</cap:certainty> 

<cap:effective>%s</cap:effective>
<cap:expires>%s</cap:expires>

<cap:description>%s</cap:description>
<cap:instruction>%s</cap:instruction>
<cap:web>%s</cap:web>
<cap:sendername>%s</cap:sendername>


"""
#Cap_info needs : event-type, urgency, serverity, certainty, effective time, expire time 


CAP_RESOURCE = """
<!-- RESOURCE -->
<cap:resource>

<cap:resourceDesc>%s</cap:resourceDesc>
<cap:mimeType>%s</cap:mimeType>  <!-- RFC 2046 compliant or http://www.iana.org/assignments/media-types/ -->
<cap:uri>%s</cap:uri>

</resource>
"""
#Cap_resource needs:  Desctiption

CAP_AREA = """
<cap:area>
<cap:areaDesc>%s</cap:areaDesc>
<cap:geoCode>%s</cap:geoCode>

<cap:polygon>
"""
#CAP_Area needs:  Description
# All CAPA_AREA_POLYGONS are assumbed to be written between CAP_AREA and CAP_AREA_END
#

CAP_AREA_END = """</cap:polygon>
</cap:area>
"""

CAP_INFO_END = """

<!-- END INFO -->
</cap:info>
"""

CAP_ALERT_END = """

<!-- END ALERT -->
</cap:alert>
"""



def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding='utf-8')



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
            valid_from = info.find('{urn:oasis:names:tc:emergency:cap:1.2}effective').text
            valid_to = info.find('{urn:oasis:names:tc:emergency:cap:1.2}expires').text
            attributes["valid_from"] = valid_from
            attributes["valid_to"] = valid_to
        file = [fname, attributes]
        #TODO- check if file is valid before appending
        files.append(file)


    # produce the xml-file

    root = Element('files')
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set(" xsi:schemaLocation", "mifare-index.xsd")

    for file in files:
        child = SubElement(root, 'file', file[1])
        child.text = file[0]

    listfilename="{0}-index.xml".format(filebase)
    listfile = open(listfilename, "w")
    listfile.write(prettify(root))
    listfile.close()




def get_urgency(date_from, now):
    """Finds the Urgency based on the valid from date
	and the current date """

    f = datetime.strptime(date_from, "%Y-%m-%dT%H:%M:00Z")
    n = datetime.strptime(now, "%Y-%m-%dT%H:00:00-00:00")

    dif = f - n

    # print "dif is ", dif, f, n, dif.total_seconds()

    if dif.total_seconds() < 0:
        return "Immediate"
    if dif.total_seconds() < 3600:
        return "Expected"

    return "Future"


def generate_file_cap_fare(filename,xmldoc,db):
        print ("generate_file_cap_fare",filename)
        res = retrieve_from_xml_fare(xmldoc)
        numAreas = 0
        sender = res['sender']
        eventname = res['eventname']
        l_type = res['type']
        mnr = res['mnr']


        fil = codecs.open(filename, 'w', 'utf-8')

        symbols = []

        now = datetime.now().strftime("%Y-%m-%dT%H:00:00-00:00")

        name = "%s at %s" % ( type, now )

        #		identifier= uuid.uuid4()
        identifier = res['id']

        fil.write(CAP_HEADING)

        fil.write(CAP_ALERT % (
                    identifier,
                    "helpdesk@met.no",
                    now,
                    l_type,
                    "Norway" )
                      )

        dt = datetime.strptime(res['vto'], "%Y-%m-%d %H:%M:%S")
        dt = dt.strftime("%Y-%m-%dT%H:%M:00Z")

        df = datetime.strptime(res['vfrom'], "%Y-%m-%d %H:%M:%S")
        df = df.strftime("%Y-%m-%dT%H:%M:00Z")

        urgency = get_urgency(dt, now)

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
                name = locs['name']
                l_id = locs['id']
                cons = locs['consequence']
                pict = locs['pictlink']
                info = locs['infolink']

                if pict:
                    fil.write(CAP_RESOURCE % ( "Grafiske beskrivelse av farevarslet", "image/png", pict))

                if info:
                        fil.write(CAP_RESOURCE % ( "Tilleggsinformasjon tilgjengelig fra andre", "text/html", info))

                for name, lon, lat in latlon:

                        if first == 0:
                            numAreas = numAreas + 1

                            #Cap_info needs : event-type, urgency, serverity, certainty, effective time, expire time
                            fil.write(CAP_INFO % (ty, urgency, sev, cer, df, dt, value, cons, "http://www.yr.no", sender  ))

                            #CAP_Area needs:  Description
                            area = unicode(CAP_AREA % (name, l_id ), "iso-8859-1")

                            fil.write(area)
                            first_lat = lat
                            first_lon = lon

                        fil.write("%f,%f,0\n" % (lon, lat))
                        first = first + 1

                fil.write("%f,%f,0\n" % (first_lon, first_lat))
                fil.write(CAP_AREA_END)

            fil.write(CAP_INFO_END)

        fil.write(CAP_ALERT_END)

        fil.close()

        print filename

        # If no areas found, remove file.
        if numAreas < 1:
             os.remove(filename)
        return 0


def generate_files_cap_fare(selectString, dateto, db, filebase):
        """Writes the given locations to a file.
           Version for CAP use.

        Structure:

                ALERT
                    |
                    | ---- One or more --  INFO
                    |						|
                    |						| -- one or more -- RESOURCE
                    |						|
                    |						| -- one or more -- AREA
                    |						|
                    |					end INFO
                    |
                end ALERT

"""

        docs = get_xml_docs(db, dateto, selectString)
        for doc in docs:

            tt=doc[1]
            tt = tt.strftime("%Y-%m-%dT%H:%M:00Z")
            filename = filebase + "_" + tt + ".cap"
            print filename
            if (os.path.isfile(filename)):
                print "File already exists!"
            else:
                xmldoc=doc[0]
                generate_file_cap_fare(filename,xmldoc,db)


        make_list_of_valid_files(filebase)
        return 0






