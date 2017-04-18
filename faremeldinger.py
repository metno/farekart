#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# Lese aktuelle kulingvarsler fra TED databasen og lage Produkt som kan vises i Diana.
#
# Author:
#  Bård Fjukstad.  Jan. 2015

"""Writes farevarsel (severe weather warning) products using data obtained
from a TED database.

  Usage: faremeldinger.py <TED db username> <passwd> <TEDDBhost> <TEDDB port> <directory for files> [directory for OpenLayers files]

KML files for Diana (and optionally OpenLayers) are created for gale warnings,
observed weather warnings and extreme weather warnings.

KML files for Diana are created for severe (dangerous) weather warnings, both
for official reports and test reports.

CAP files are created for official severe weather warnings.

KML file creation is handled by the fare_common module. CAP file creation is
handled by the generatecap_fare module.

The base URL used for the CAP.rss generated file can be overridden by setting
the CAP_BASE_URL environment variable.

The directory used to publish the CAP files, RSS file and XSLT stylesheets is,
by default, a subdirectory in the output directory called "publish". This can
be overridden by setting the CAP_PUBLISH_DIR environment variable.
"""

import os, sys, time
import MySQLdb, shutil

from metno_fare.fare_common import *
from metno_fare.generatecap_fare import generate_files_cap_fare
from metno_fare import publishcap


if __name__ == "__main__":

    if not 6 <= len(sys.argv) <= 8:
        sys.stderr.write("Usage: %s <TED db username> <passwd> <TEDDBhost> <TEDDB port> <directory for files> <Optional: Directory for schemas> <Optional: OpenLayerDir>\n" % sys.argv[0])
        sys.exit(1)

    db = MySQLdb.connect(user=sys.argv[1],
                         passwd=sys.argv[2],
                         host=sys.argv[3],
                         port=int(sys.argv[4]),
                         db="ted")

    dirname = sys.argv[5]

    if not os.path.exists(dirname):
        os.mkdir(dirname)

    if len(sys.argv) > 6:
        schema_dirname = sys.argv[6]
    else:
        if os.path.exists("schemas"):
            schema_dirname = "schemas"
        else:
            schema_dirname = "/usr/share/xml/farekart"

        
    OpenLayer = False

    if len(sys.argv) > 7:
        ol_dirname = sys.argv[7]
        OpenLayer = True
        if not os.path.exists(ol_dirname):
            os.mkdir(ol_dirname)


    # Farevarsler in CAP format
    fare_documentname="METfare"

    dirname_v1 = os.path.join(dirname, "v1")
    if (not os.path.isdir(dirname_v1)):
        os.mkdir(dirname_v1)
    generate_files_cap_fare(fare_documentname,dirname, schema_dirname,db)
    generate_files_cap_fare(fare_documentname,dirname_v1, schema_dirname,db,make_v1=True)

    dirnames = [dirname, dirname_v1]
    for dir in dirnames:
        #generate RSS-file
        pass

    # Generate an RSS file to describe the CAP files created.
    filebase = os.path.join(dirname,  fare_documentname)
    rss_file = "CAP.rss"
    output_dir = os.getenv("CAP_PUBLISH_DIR", dirname)
    base_url = os.getenv("CAP_BASE_URL", "http://api.met.no/CAP")
    publishcap.main(filebase,rss_file, dirname, output_dir, base_url)
    if dirname != output_dir:
        shutil.copy2(os.path.join(dirname, 'CAP_en.json'), os.path.join(output_dir, 'CAP_en.json'))
        shutil.copy2(os.path.join(dirname, 'CAP_no.json'), os.path.join(output_dir, 'CAP_no.json'))


    sys.stderr.write("Start creating kml-files\n")
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

    # same from other product.
    
    select_string='select value,termin,lang from document where name = "METfare" and vto > %s'

    filename = os.path.join(dirname, "Current_METfare.kml")

    generate_file_fare(db, filename, "Dangerous weather warning", "Label Faremelding", now, select_string)

    # Farevarsler TEST

    select_string='select value from document where name = "x_test_MIfare" and vto > %s'

    filename = os.path.join(dirname, "Current_fare_test.kml")

    generate_file_fare(db, filename, "Dangerous weather warning", "Label Faremelding", now, select_string)

    # Close the database connection.

    if db:
        db.close()


    sys.exit()
