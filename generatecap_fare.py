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

"""
#Cap_info needs : event-type, urgency, serverity, certainty, effective time, expire time 


CAP_RESOURCE = """
<!-- RESOURCE -->
<cap:resource>

<cap:resourceDesc>%s</cap:resourceDesc>
<cap:mimeType>%s</cap:mimeType>  <!-- RFC 2046 compliant or http://www.iana.org/assignments/media-types/ -->

</resource>
"""
#Cap_resource needs:  Desctiption

CAP_AREA = """
<cap:area>
<cap:areaDesc>%s</cap:areaDesc>

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

def generate_file_cap_fare( selectString, dateto, db, filename, type, labelType ):
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


	doc = get_xml_doc( db, dateto, selectString)
	
	results = retrieve_from_xml( doc )
	
	numAreas = 0

	fil = codecs.open(filename,'w','utf-8')

	symbols = []

	now = time.strftime("%Y-%m-%dT%H:00:00-00:00")

	name = "%s at %s" % ( type, now )

	randomIdentifier= uuid.uuid4()

	fil.write(CAP_HEADING )

	fil.write(CAP_ALERT % (
				randomIdentifier, 
				"helpdesk@met.no",
				now,
				type,
				"Norway" )
			  )


	for i in results:
	
		res = results[i]
	
		dt = time.strptime(res['vto'],"%Y-%m-%d %H:%M:%S")
		dt = time.strftime("%Y-%m-%dT%H:%M:00Z",dt)
		
		df = time.strptime(res['vfrom'],"%Y-%m-%d %H:%M:%S")
		df = time.strftime("%Y-%m-%dT%H:%M:00Z",df)

		for p in res['locations']:
		
		  locs = res['locations'][p]
	  
		  for n in locs['id'].split(":"):
		  
			latlon = get_latlon(n,db)
			first = 0
			value = locs['varsel']
			comm =  locs['kommentar']
			sev  =  locs['severity']
	
			ty  =  locs['type']
			cer  =  locs['certainty']
			tri  =  locs['triggerlevel']
			eng  =  locs['english']
		
			for name,lon,lat in latlon:
				
				if first == 0:
					numAreas = numAreas + 1

					#Cap_info needs : event-type, urgency, serverity, certainty, effective time, expire time 
					fil.write(CAP_INFO % (ty, "Expected",sev, cer, df, dt  ))
	
					#CAP_Area needs:  Description
					area = unicode(CAP_AREA % value, "iso-8859-1")
					
					fil.write(area)
					first_lat = lat
					first_lon = lon
					
				fil.write("%f,%f,0\n"%(lon,lat))
				first= first + 1
		
			fil.write("%f,%f,0\n"%(first_lon,first_lat))
			fil.write(CAP_AREA_END)
	
			fil.write(CAP_INFO_END)

	fil.write(CAP_ALERT_END)

	fil.close()

	# If no areas found, remove file.
	if numAreas < 1:
		os.remove(filename)

	return 0

