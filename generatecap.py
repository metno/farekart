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
import codecs
import sys
import uuid
import time
import os

import fare_utilities

CAP_HEADING = """<?xml version = '1.0' encoding = 'UTF-8' standalone = 'yes'?>

"""

CAP_ALERT = """
<!-- ALERT -->
<cap:alert xmlns:cap="urn:oasis:names:tc:emergency:cap:1.2"> 

<!-- Mandatory elements -->
<cap:identifier>%s</cap:identifier>  <!-- Must uniquely identify this message -->
<cap:sender>%s</cap:sender> <!-- Identifies originator of alert -->
<cap:sent>%s</cap:sent>  <!-- "2002-05-24T16:49:00-00:00". No timezone literal, only hours -00:00 is UTC-->
<cap:status>Actual</cap:status> <!-- Actual, Exercise, System, Test, Draft -->
<cap:msgType>Alert</cap:msgType> <!-- Alert, Update, Cancel, Ack, Error -->
<cap:scope>Public</cap:scope>  <!-- Public, Restricted, Private -->

<!-- Optional elements -->
<cap:note>%s alert for %s issued by the Norwegian Meteorological Institute</cap:note>
<!-- <restriction><addresses><source><code><note><refereces><incidents> -->

<!-- An ALERT element may contain one or more INFOR elements -->

"""
#Cap_alert needs : Identifier, sender, sent-datetime, note-type, note-areaname

CAP_ALERT_CLEAN = """
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
#Cap_alert_clean needs : Identifier, sender, sent-datetime, note-type, note-areaname

CAP_INFO = """
<!-- INFO -->
<cap:info>

<!-- Mandatory elements -->
<cap:category>Met</cap:category>  <!-- Geo, Met, Safety, Security, Rescue, Fire, Health, Env, Transport, Infra, CBRNE chem Bio Radio Nuclear Explosive -->
<cap:event>%s</cap:event>
<cap:urgency>Expected</cap:urgency>  <!-- Immediate, Expected, Future, Past, Unknown -->
<cap:severity>Moderate</cap:severity> <!-- Extreme, Severe, Moderate, Minor, Unknown -->
<cap:certainty>Likely</cap:certainty> <!-- Observed, Likely p> 50percent, Possible p <= 50percent, Unlikely, Unknown -->

<!-- Optional elements -->
<!-- <language><responseType><audience><eventCode><effective time><onset time><expires time><senderName><headline><description><instruction><web><contact><parameter> -->
<cap:effective>%s</cap:effective>
<cap:expires>%s</cap:expires>

<!-- An INFO element may contain zero or more RESOURCE og AREA elements -->

"""
#Cap_info needs : event-type, effective time, expire time 

CAP_INFO_CLEAN = """
<cap:info>

<cap:category>Met</cap:category>
<cap:event>%s</cap:event>
<cap:urgency>Expected</cap:urgency>
<cap:severity>Moderate</cap:severity>
<cap:certainty>Likely</cap:certainty> 

<cap:effective>%s</cap:effective>
<cap:expires>%s</cap:expires>

"""
#Cap_info_clean needs : event-type, effective time, expire time 


CAP_RESOURCE = """
<!-- RESOURCE -->
<cap:resource>

<!-- Mandatory elements -->
<cap:resourceDesc>%s</cap:resourceDesc>
<cap:mimeType>%s</cap:mimeType>  <!-- RFC 2046 compliant or http://www.iana.org/assignments/media-types/ -->

<!-- Optional elements -->
<!-- possible: <size><uri><derefUri><digest SHA-1 per FIPS 180-2> -->


</resource>
"""
#Cap_resource needs:  Desctiption

CAP_AREA = """
<!-- AREA -->
<cap:area>

<!-- Mandatory elements -->
<cap:areaDesc>%s</cap:areaDesc>

<!-- Optional elements -->
<!-- possible: <polygon><circle><geodode><altitude><ceiling> -->

<cap:polygon>  <!-- white space delimited list of WGS 84 coordinate pairs. A minimum of 4 and first and last must be the same. Multiple instances of Polygon may occur within an area block. EPSG 4326 equivalent -->
"""
#CAP_Area needs:  Description
# All CAPA_AREA_POLYGONS are assumbed to be written between CAP_AREA and CAP_AREA_END
#
CAP_AREA_CLEAN = """
<cap:area>
<cap:areaDesc>%s</cap:areaDesc>

<cap:polygon>
"""
#CAP_Area_clean needs:  Description
# All CAPA_AREA_POLYGONS are assumbed to be written between CAP_AREA and CAP_AREA_END
#

CAP_AREA_END = """</cap:polygon>

<!-- Other options
  circle   WGS 84 coordinate pair forlowed by space and a radius value in km. 
  geocode
  altitude  feet above mean sea level pr WGS 84 datum
  ceiling   feet aboce mean sea level pr WGS 84 datum
  -->


</cap:area>
"""

CAP_AREA_END_CLEAN = """</cap:polygon>
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

def generate_file_cap( locations, db, filename, type, labelType ):
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

	numAreas = 0

	fil = codecs.open(filename,'w','utf8')
	fil2 = codecs.open(filename + "clean.txt",'w','utf8')

	symbols = []

	now = time.strftime("%Y-%m-%dT%H:00:00-00:00")

	name = "%s warnings at %s" % ( type, now )

	randomIdentifier= uuid.uuid4()

	fil.write(CAP_HEADING )
	fil2.write(CAP_HEADING )

	fil.write(CAP_ALERT % (
				randomIdentifier, 
				"helpdesk@met.no",
				now,
				type,
				"Norway" )
			  )

	fil2.write(CAP_ALERT_CLEAN % (
				randomIdentifier, 
				"helpdesk@met.no",
				now,
				type,
				"Norway" )
			  )


	for n in range(len(locations)):

		varsel = locations[n]
		dateto=varsel[2]
		vname = varsel[0]
		desc = varsel[4]
		symbname = ""

		locs = varsel[3]

		fil.write(CAP_INFO % (type, now, dateto.strftime("%Y-%m-%dT%H:%M:00-00:00") ) )
		fil2.write(CAP_INFO_CLEAN % (type, now, dateto.strftime("%Y-%m-%dT%H:%M:00-00:00") ) )


		for n in locs.split(":"):

			latlon = fare_utilities.get_latlon(n,db)
			first = 0
			for name,lon,lat in latlon:
	
				if first == 0:
					firstlat = lat
					firstlon = lon

					fil.write(repr(CAP_AREA % name))
					fil2.write(repr(CAP_AREA_CLEAN % name))

					numAreas = numAreas + 1

				fil.write("%f,%f\n"%(lon,lat))
				fil2.write("%f,%f\n"%(lon,lat))
				first= first + 1

			# Write first location as last also
			fil.write("%f,%f\n"%(firstlon,firstlat))
			fil2.write("%f,%f\n"%(firstlon,firstlat))

			fil.write(CAP_AREA_END)
			fil2.write(CAP_AREA_END_CLEAN)

		fil.write(CAP_INFO_END)
		fil2.write(CAP_INFO_END)

	fil.write(CAP_ALERT_END)
	fil2.write(CAP_ALERT_END)

	fil.close()
	fil2.close()

	# If no areas found, remove file.
	if numAreas < 1:
		os.remove(filename)
		os.remove(filename+"clean.txt")

	return 0

