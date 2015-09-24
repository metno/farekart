#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# test av kartverkets GEOJSON grenser
#
#
# Author:
#  Bård Fjukstad.  Jan. 2015
#
import json


json_data = open("stedsnavn.geojson")
data = json.load(json_data)

#Stedsnavn er 0 .. 1048343   dvs > 1 mill steder


utdata = {}

for n in range(1048344):

	key =  "%f,%f" % ( data["features"][n]['geometry']['coordinates'][0],data["features"][n]['geometry']['coordinates'][0] )
	sted = [ data["features"][n]['properties']['for_snavn'],
			data["features"][n]['properties']['kom_fylkesnr'],
			data["features"][n]['properties']['enh_komm']]


	utdata[key] = sted

# print utdata

for key in utdata:

	print key,"%s\t%d\t%d" %( utdata[key][0],utdata[key][1],utdata[key][2])



