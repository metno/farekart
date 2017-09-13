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

"""Generates Common Alerting Protocol (CAP) files for farevarsel (dangerous
weather warning) reports obtained from a TED database."""

import linecache
import os
import sys
import MySQLdb

import dateutil.parser

from lxml import etree
from generatejson_fare import make_list_of_valid_files
from generate_capalert import generate_capalert_fare
from generate_capalert_v1 import generate_capalert_v1
import publishcap

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    return 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)



def get_ted_docs(db, select_string):
    """Retrieves a full set of documents from the database, db, using the given
    SQL select_string. """

    try:
        cur = db.cursor()
        cur.execute(select_string)
        result = cur.fetchall()

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        return None

    return result


def generate_capfiles_from_teddir(ted_directory,output_dirname,db,make_v1=False):
    filenames = os.listdir(ted_directory)
    for ted_filename in filenames:
        generate_capfile_from_tedfile(os.path.join(ted_directory,ted_filename),output_dirname,db,make_v1)


def generate_capfile_from_tedfile(ted_filename,output_dirname,db,make_v1=False):
    """reads the tedfile with the given filename
    writes cap-file, the name is given by the termin time and product name of the ted document
    """
    try:
    # open tedDocument file for reading
        with open(ted_filename,'r') as f:
            generate_capfile_from_teddoc(f.read(),output_dirname,db,make_v1)

    except Exception as inst:
        sys.stderr.write("File %s could not be converted to CAP: %s \n" % (ted_filename, PrintException()))

def generate_capfile_from_teddoc(xmldoc, output_dirname,db,make_v1=False):
    cap_filename = ""
    try:
        # find correct file name from the tedDocuments name and termin
        cap_filename= get_capfilename_from_teddoc(xmldoc)
        cap_filename = os.path.join(output_dirname, cap_filename)
        sys.stderr.write("File '%s' will be generated\n" % (cap_filename))

        if (make_v1):
            # Test make capalert version 1
            # generate the CAP alert  from the tedDocument
            capalert = generate_capalert_v1(xmldoc, db)
        else:
            # generate the CAP alert  from the tedDocument
            capalert = generate_capalert_fare(xmldoc, db)

        # write the resulting CAP alert to file
        with open(cap_filename,'w') as f:
            f.write(capalert)


    except Exception as inst:
        sys.stderr.write("CAP file %s could not be made: %s %s \n" % (cap_filename, PrintException() ,inst.message))


def get_capfilename_from_teddoc(xmldoc):
    root = etree.fromstring(xmldoc)
    for p in root.iter('productdescription'):
        termin = p.get('termin')
        prodname=p.get('prodname')

    ts = dateutil.parser.parse(termin).strftime("%Y%m%dT%H%M%S")
    filename= "%s-%s.cap.xml" % (prodname,ts)
    return filename


def generate_files_cap_fare(ted_documentname, output_dirname, schemas,db,make_v1=False):
    """Generates CAP files for the warnings obtained from the database, db,
    for documents with
    Writes an index file for all CAP files in output_dirname."""

    generate_capfiles_from_teddb(ted_documentname,output_dirname,db,make_v1)
    filebase = os.path.join(output_dirname,ted_documentname)
    make_list_of_valid_files(filebase, schemas,make_v1)



def download_ted_documents(download_dirname,ted_documentname,db):
    docs = get_ted_documents(db, ted_documentname)
    for doc in docs:
        # write ted-file
        lang = doc[2]
        termin = doc[1].strftime("%Y-%m-%d-%H-%M-%S")
        tedfilename = "%s-%s-%s.xml" % (ted_documentname, termin, lang)
        tedfilename = os.path.join(download_dirname, tedfilename)
        sys.stderr.write(tedfilename + "\n")

        with open(tedfilename,'w') as f:
            f.write(doc[0])


def get_ted_documents(db, ted_documentname):
    select_string = 'select value,termin,lang from document where name = "%s" and status != "tempo"' % ted_documentname
    docs = get_ted_docs(db, select_string)
    return docs


def generate_capfiles_from_teddb(ted_documentname,output_dirname,db,make_v1):
    docs = get_ted_documents(db, ted_documentname)
    for doc in docs:
        capfilename = os.path.join(output_dirname,get_capfilename_from_teddoc(doc[0]))
        if (os.path.isfile(capfilename)):
            sys.stderr.write("File '%s' already exists!\n" % capfilename)
        else:
            generate_capfile_from_teddoc(doc[0], output_dirname, db,make_v1)



if __name__ == "__main__":

    if not 6 <= len(sys.argv) <= 9:
        sys.stderr.write("Usage: %s <TED db username> <passwd> <TEDDBhost> <TEDDB port> <directory for CAP/Json output files>\n"
                         "<Optional: file or directory of tedDocuments to convert to CAP>\n"
                         "<Optional: directory for downloading tedDocuments from database>\n"
                         "<Optional: tedDocument name to download from database (default METfare)>\n"
                         % sys.argv[0])
        sys.exit(1)

    db = MySQLdb.connect(user=sys.argv[1],
                         passwd=sys.argv[2],
                         host=sys.argv[3],
                         port=int(sys.argv[4]),
                         db="ted")

    output_dirname = sys.argv[5]
    if not os.path.exists(output_dirname):
        os.mkdir(output_dirname)

    if len(sys.argv) > 6:
       ted_filename=sys.argv[6]
    else:
        ted_filename = None


    if len(sys.argv) > 7:
       download_dirname=sys.argv[7]
    else:
        download_dirname = None


    if len(sys.argv) > 8:
       ted_documentname=sys.argv[8]
    else:
       ted_documentname ="METfare"


    if os.path.exists("schemas"):
        schema_dirname = "schemas"
    else:
        schema_dirname = "/usr/share/xml/farekart"

    if download_dirname == None:
        sys.stderr.write("Do not download files\n")
    elif os.path.isfile(download_dirname):
        sys.stderr.write("Do not download files, %s is a file not directory\n"%download_dirname)
    else:
        if not os.path.exists(download_dirname):
            os.mkdir(download_dirname)
        sys.stderr.write(("Download files to directory %s\n") % download_dirname)
        download_ted_documents(download_dirname,ted_documentname,db)

    if ted_filename == None:
        #read xml from the database
        sys.stderr.write("Filename is None\n")
        generate_capfiles_from_teddb(ted_documentname,output_dirname,db,True)
    elif os.path.isfile(ted_filename):
        sys.stderr.write("File %s will be converted to CAP\n" % ted_filename)
        generate_capfile_from_tedfile(ted_filename,output_dirname,db,True)
    elif os.path.isdir(ted_filename):
        sys.stderr.write("Directory %s should be converted to CAP\n" % ted_filename)
        generate_capfiles_from_teddir(ted_filename,output_dirname,db,True)
    else:
        sys.stderr.write("%s is not a file or directory. No conversion is done\n" % ted_filename)
        exit


    filebase = os.path.join(output_dirname,ted_documentname)
    make_list_of_valid_files(filebase, schema_dirname,True)
    # should be the directory to publish CAP
    publishcap.main(output_dirname)
