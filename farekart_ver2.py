#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# Lese aktuelle kulingvarsler fra TED databasen og lage generisk KML produkt
#
# Author:
#  Bård Fjukstad.  Jan. 2015

import sys
import MySQLdb
import time
import os

from lxml import etree
from pykml.factory import KML_ElementMaker as KML

#local imports.
from fare_utilities import *
from generatecap import *
from faremeldinger import *


# Trying to use pyKML package, example of use is from
#   https://pythonhosted.org/pykml/examples/misc_examples.html#example-using-pykml-to-visualize-ephemeris-data
#

def generate_new_kml( locations, db, filename, warning_type, label ):
    """Generate a KML file using the pyKML package. """

    doc = KML.kml(
        KML.Document(
            KML.Name( warning_type ),
            KML.Style(







#
# MAIN
#
if __name__ == "__main__":

	if len(sys.argv) < 4:
		print "Wrong number of arguments\nUsage faremeldinger.py <TED db username> <passwd> <directory for files>"
		exit(1)

	db = MySQLdb.connect(host="teddb",
						user=sys.argv[1],
						passwd=sys.argv[2],
						db="ted",
						port=19400)

	dirname = sys.argv[3]

	now = time.strftime("%Y-%m-%d %H:%M:00")
### Gale Warnings

	select_string="select name,vfrom,vto,location, value from forecast where lang=\"EN\" and vto > \"%s \" and name =\"MIkuling\" order by vto desc" % now

	locations = get_locations(db, select_string)

	generate_file( locations,db, "%s/Current_gale.kml" %  dirname, "Gale warning", "Label Gale" )

	generate_file_ol( locations,db, "/var/www/html/data/Current_gale.kml", "Gale warning", "Label Gale" )

	generate_file_cap(locations,db, "/var/www/html/data/Current_gale.cap.txt", "Gale warning", "Gale Warning")

### OBS warnings

	select_string="select name,vfrom,vto,location, value from forecast where vto > \"%s \" and name in (\"VA_Obsvarsel\",\"VV_Obsvarsel\",\"VN_Obsvarsel\") order by vto desc" % now

	locations = get_locations(db, select_string)

	generate_file(locations,db, "%s/Current_obs.kml" % dirname, "Obs warning", "Label Obs")

	generate_file_ol(locations,db, "/var/www/html/data/Current_obs.kml", "Obs warning", "Label Obs")

	generate_file_cap(locations,db, "/var/www/html/data/Current_obs.cap.txt", "Obs warning", "Severe weather")

### Extreme forecasts

	select_string="select name,vfrom,vto,location, value from forecast where vto > \"%s \" and name in (\"MIekstrem_FaseA\",\"MIekstrem\") order by vto desc" % now

	locations = get_locations(db, select_string)

	generate_file(locations,db, "%s/Current_extreme.kml" % dirname, "Extreme forecast", "Label Extreme")

	generate_file_ol(locations,db, "/var/www/html/data/Current_extreme.kml", "Extreme forecast", "Label Extreme")

	generate_file_cap(locations,db, "/var/www/html/data/Current_extreme.cap.txt", "Extreme forecast", "Extreme weather")


## Close

	if db:
		db.close()
 
