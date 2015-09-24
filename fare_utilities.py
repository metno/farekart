#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# Utilities for å lese aktuelle kulingvarsler fra TED databasen og lage Produkt som kan vises i DIANA.
#
#
# Author:
#  Bård Fjukstad.  Jan. 2015
#
import sys
import MySQLdb
import time
import os



def get_latlon(n,db):
	"""Retrieves the Geographical corners for the given TED defined area ID"""

	select_string ="select name, corners from location where id = \"%s\"" % n

	try:
		cur = db.cursor()
		cur.execute(select_string)
		result = cur.fetchone()

	except MySQLdb.Error, e:
	    print "Error %d: %s" % (e.args[0], e.args[1])
	
	retval = []

	name = result[0]

	for n in result[1].split(":"):

		o,p = n.split(" ")

		lo = int(o) / 10000.0
		la = int(p) / 10000.0
		
		lon = int(lo) + ( (lo - int(lo) )*100.0/60.0 )

		lat = int(la) + ( (la - int(la) )*100.0/60.0 )

		retval.append((name,lon,lat))

	return retval

def copyToWWW( filename ):
	"""Copies a file to  /var/www/data for use on local web server 
	    Function not used, replaced by new generation for Openlayers use"""

	cmd = "cp %s /var/www/data/" % filename

	os.system(cmd)

	return 0

