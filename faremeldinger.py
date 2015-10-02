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

import os, sys, time
import MySQLdb

from fare_common import *
from generatecap_fare import generate_files_cap_fare


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

    # Gale Warnings

    select_string = 'select name,vfrom,vto,location,value from forecast where lang="EN" and vto > %s and name="MIkuling" order by vto desc'

    locations = get_locations(db, select_string, now)

    filename = os.path.join(dirname, "Current_gale.kml")

    generate_file(locations, db, filename, "Gale warning", "Label Gale")

    if OpenLayer:
        filename = os.path.join(ol_dirname, "Current_gale_ol.kml")
        generate_file_ol(locations,db, filename, "Gale warning", "Label Gale")

    # OBS warnings

    select_string = 'select name,vfrom,vto,location,value from forecast where vto > %s and name in ("VA_Obsvarsel","VV_Obsvarsel","VN_Obsvarsel") order by vto desc'

    locations = get_locations(db, select_string, now)

    filename = os.path.join(dirname, "Current_obs.kml")

    generate_file(locations, db, filename, "Obs warning", "Label Obs")

    if OpenLayer:
        filename = os.path.join(ol_dirname, "Current_obs_ol.kml")
        generate_file_ol(locations,db, filename, "Obs warning", "Label Obs")

    # Extreme forecasts

    select_string='select name,vfrom,vto,location,value from forecast where vto > %s and name in ("MIekstrem_FaseA","MIekstrem") order by vto desc'

    locations = get_locations(db, select_string, now)

    filename = os.path.join(dirname, "Current_extreme.kml")

    generate_file(locations, db, filename, "Extreme forecast", "Label Extreme")

    if OpenLayer:
        filename = os.path.join(ol_dirname, "Current_extreme_ol.kml")
        generate_file_ol(locations, db, filename, "Extreme forecast", "Label Extreme")

    # Farevarsler

    select_string='select value,termin from document where name = "MIfare" and vto > %s'

    filename = os.path.join(dirname, "Current_fare.kml")

    generate_file_fare(db, filename, "Dangerous weather warning", "Label Faremelding", now, select_string)

    filebase = os.path.join(dirname, "MIfare")
    generate_files_cap_fare(select_string, now, db, filebase)

    # Farevarsler TEST

    select_string='select value from document where name = "x_test_MIfare" and vto > %s'

    filename = os.path.join(dirname, "Current_fare_test.kml")

    generate_file_fare( db, filename, "Dangerous weather warning", "Label Faremelding", now, select_string )

    # Close the database connection.

    if db:
        db.close()
