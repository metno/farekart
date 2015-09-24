#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# Lese aktuelle kulingvarsler fra TED databasen og lage Produkt som kan vises i DIANA.
#
# Author:
#  Bård Fjukstad.  Jan. 2015

import sys
import MySQLdb
import time
import os

from fare_utilities import *
from generatecap import *
from generatecap_fare import *
from faremeldinger_v2 import *

KML_HEADING = """<?xml version="1.0" encoding="iso-8859-1"?>

<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
"""

KML_END = """  </Document>
</kml>
"""

KML_VALIDLABEL = """    <Placemark>
      <name>Valid warnings at:</name>
      <ExtendedData>
        <Data name="met:objectType">
          <value>Text</value>
        </Data>
        <Data name="met:style:type">
          <value>Dangerous weather warning</value>
        </Data>
        <Data name="met:text">
          <value>GYLDIGE ADVARSLER PR
%s</value>
        </Data>
        <Data name="met:spacing">
          <value>0.5</value>
        </Data>
        <Data name="met:margin">
          <value>4</value>
        </Data>
      </ExtendedData>
      <Polygon>
        <tessellate>1</tessellate>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>-3.16288,75.7207,0
15.9619,74.349,0
</coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
"""

KML_VALIDLABEL_OL = """    <Placemark>
      <name>Valid warnings at:</name>
          <Point>
            <coordinates>-3.16288,75.7207,0</coordinates>
          </Point>
          <description>GYLDIGE ADVARSLER PR
%s</description>
      <ExtendedData>
        <Data name="met:objectType">
          <value>Text</value>
        </Data>
        <Data name="met:style:type">
          <value>Dangerous weather warnig</value>
        </Data>
        <Data name="met:text">
          <value>GYLDIGE ADVARSLER PR
%s</value>
        </Data>
        <Data name="met:spacing">
          <value>0.5</value>
        </Data>
        <Data name="met:margin">
          <value>4</value>
        </Data>
      </ExtendedData>
    </Placemark>
"""

KML_AREA = """    <Placemark>
      <name>%s</name>
      <description>
      %s
      </description>
      <TimeSpan>
    	<begin>%s</begin>
    	<end>%s</end>
      </TimeSpan>
      <ExtendedData>
        <Data name="met:objectType">
          <value>PolyLine</value>
        </Data>
        <Data name="met:style:type">
          <value>Gale warning</value>
        </Data>
        <Data name="met:info:type">
          <value>Gale warning</value>
        </Data>
        <Data name="met:style:fillcolour">
          <value>yellow</value>
        </Data>
        <Data name="met:info:severity">
          <value>yellow</value>
        </Data>	
      </ExtendedData>
      <Polygon>
        <tessellate>1</tessellate>
        <outerBoundaryIs>
          <LinearRing>
           <coordinates>"""


KML_AREA_END = """            </coordinates>         
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
"""

KML_TEXT = """    <Placemark>
      <name>%s</name>
      <ExtendedData>
        <Data name="met:objectType">
          <value>Text</value>
        </Data>
        <Data name="met:style:type">
          <value>%s</value>
        </Data>
        <Data name="met:text">
          <value>%s</value>
        </Data>
        <Data name="met:spacing">
          <value>0.5</value>
        </Data>
        <Data name="met:margin">
          <value>4</value>
        </Data>
      </ExtendedData>
      <Polygon>
        <tessellate>1</tessellate>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>%f,%f,0
%f,%f,0
</coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
"""
KML_TEXT_OL = """    <Placemark>
     <name>%s</name>
     <Point>
     	<coordinates>%f,%f,0</coordinates>
     </Point>
    </Placemark>
"""

def get_locations(db, select_string ):
	"""Retrieve all currently valid GALE forecasts from the TED db"""

	try:
		cur = db.cursor()
		cur.execute(select_string)
		result = cur.fetchall()

	except MySQLdb.Error, e:
	    print "Error %d: %s" % (e.args[0], e.args[1])
	
	return result


def generate_file( locations, db, filename, type, labelType ):
	"""Writes the given locations to a file. First as AREAS then as LABELs"""

	fil = open(filename,'w')

	fil.write(KML_HEADING)

	for n in range(len(locations)):

		varsel = locations[n]
		vname = varsel[0]
		datefrom=varsel[1]
		dateto=varsel[2]
		locs = varsel[3]
		value = varsel[4]
		value = value.replace("<in>","")		# Strip som tags from TED
		value = value.replace("</in>","")		# Strip som tags from TED

		dt = dateto.strftime("%Y-%m-%dT%H:%M:00Z")
		df = datefrom.strftime("%Y-%m-%dT%H:%M:00Z")
    
		for n in locs.split(":"):

			latlon = get_latlon(n,db)
			first = 0
			for name,lon,lat in latlon:
	
				if first == 0:
					fil.write(KML_AREA % (name,value,df,dt)) #name, description, vfrom,vto 
					first_lat = lat
					first_lon = lon
					
				fil.write("%f,%f,0\n"%(lon,lat))
				first= first + 1

			fil.write("%f,%f,0\n"%(first_lon,first_lat))
			fil.write(KML_AREA_END)

	fil.write(KML_END)

	fil.close()

	return 0

def generate_file_ol( locations, db, filename, type, labelType ):
	"""Version for OpenLayers use.
	   Writes the given locations to a file. First as AREAS then as LABELs"""

	fil = open(filename,'w')

	symbols = []

	now = time.strftime("%Y-%m-%d %H:00")

	name = "%s warnings at %s" % ( type, now )

	fil.write(KML_HEADING)

#	fil.write(KML_VALIDLABEL_OL % (now,now) )

	for n in range(len(locations)):

		varsel = locations[n]
		vname = varsel[0]
		datefrom=varsel[1]
		dateto=varsel[2]
		locs = varsel[3]
		value = varsel[4]
		value.replace("<in>","")		# Strip som tags from TED
		value.replace("</in>","")		# Strip som tags from TED
		# symbname = ""

		for n in locs.split(":"):

			latlon = get_latlon(n,db)
			first = 0
			lattop = 0
			latbot = 90
			lontop = 0
			lonbot = 180
			for name,lon,lat in latlon:
	
				if first == 0:
					fil.write(KML_AREA % (name,value +" Valid to: " + str(dateto),datefrom,dateto)) #name, description, vfrom,vto 
					symbname = name + " " + value + " " + str(dateto)
					first_lat = lat
					first_lon = lon

				if lat > lattop: lattop = lat
				if lat < latbot: latbot = lat
				if lon > lontop: lontop = lon
				if lon < lonbot: lonbot = lon

				fil.write("%f,%f,0\n"%(lon,lat))
				first= first + 1

			slat = latbot + (lattop - latbot )/2.0
			slon = lonbot + (lontop - lonbot )/2.0

			symbols.append((vname,symbname,dateto,slat,slon))

			fil.write("%f,%f,0\n"%(first_lon,first_lat))
			fil.write(KML_AREA_END)

	for n in range(len(symbols)):

		sentral,omrade,tidto,slat,slon = symbols[n]
		
		tekst = "%s %s" %( omrade, tidto.strftime("%Y-%m-%d %H:%M") )
		
		fil.write(KML_TEXT_OL % ( tekst, float(slon), float(slat) ) )

	fil.write(KML_END)

	fil.close()

	return 0

#
# MAIN
#
if __name__ == "__main__":

	if len(sys.argv) < 6:
		print "Wrong number of arguments\nUsage faremeldinger.py <TED db username> <passwd> <TEDDBhost> <TEDDB port> <directory for files> <Optional: OpenLayerDir>"
		exit(1)

	db = MySQLdb.connect(user=sys.argv[1],
						passwd=sys.argv[2],
						host=sys.argv[3],
						port=int(sys.argv[4]),
						db="ted",
						)

	dirname = sys.argv[5]
	OpenLayer = False
    
	if len(sys.argv) >6:
		ol_dirname = sys.argv[6]
		OpenLayer = True

	now = time.strftime("%Y-%m-%d %H:%M:00")

### Gale Warnings

	select_string="select name,vfrom,vto,location, value from forecast where lang=\"EN\" and vto > \"%s \" and name =\"MIkuling\" order by vto desc" % now

	locations = get_locations(db, select_string)

	filename = "%s/Current_gale.kml" %  dirname

	generate_file( locations,db, filename, "Gale warning", "Label Gale" )

	if OpenLayer:
		filename = "%s/Current_gale_ol.kml" % dirname
		generate_file_ol( locations,db, filename, "Gale warning", "Label Gale" )

### OBS warnings

	select_string="select name,vfrom,vto,location, value from forecast where vto > \"%s \" and name in (\"VA_Obsvarsel\",\"VV_Obsvarsel\",\"VN_Obsvarsel\") order by vto desc" % now

	locations = get_locations(db, select_string)

	filename = "%s/Current_obs.kml" % dirname

	generate_file(locations,db, filename, "Obs warning", "Label Obs")

	if OpenLayer:
		filename = "%s/Current_obs_ol.kml" % dirname
		generate_file_ol(locations,db, filename, "Obs warning", "Label Obs")

### Extreme forecasts

	select_string="select name,vfrom,vto,location, value from forecast where vto > \"%s \" and name in (\"MIekstrem_FaseA\",\"MIekstrem\") order by vto desc" % now

	locations = get_locations(db, select_string)

	filename = "%s/Current_extreme.kml" % dirname

	generate_file(locations,db, filename, "Extreme forecast", "Label Extreme")

	if OpenLayer:
		filename = "%s/Current_extreme_ol.kml" % dirname
		generate_file_ol(locations,db, filename, "Extreme forecast", "Label Extreme")

### Farevarsler

 	select_string="select value,termin from document where name = \"MIfare\" and vto > \"%s \" " %	now

	filename = "%s/Current_fare.kml" %  dirname

	generate_file_fare( db, filename, "Dangerous weather warning", "Label Faremelding", now, select_string )

	filebase = "%s/MIfare" %  dirname

	generate_files_cap_fare(select_string,  now ,db, filebase)

### Farevarsler TEST

 	select_string="select value from document where name = \"x_test_MIfare\" and vto > \"%s \" " % now

	filename = "%s/Current_fare_test.kml" %  dirname

	generate_file_fare( db, filename, "Dangerous weather warning", "Label Faremelding", now, select_string )


## Close

	if db:
		db.close()
