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

import glob, os, sys, uuid
from datetime import datetime
import dateutil.parser

from lxml.etree import Element, SubElement, tostring
from lxml import etree
import json

from metno_fare.fare_common import *
from metno_fare import publishcap

# Define characters to be removed from values from the database.
invalid_extra_chars = " ,."

# Define values to compare certainty and severity text against. We will
# compare both fields against a common set so that a correct subsitution will
# be made if the original text was close enough, but when a value from the
# wrong field is used (a severity of "Possible", for example), the substituted
# value will be invalid and will cause the later CAP validation to correctly
# fail. This ensures that we don't happily accept certainty values in the
# severity field and vice versa.
predefined_severity = set(["Extreme", "Severe", "Moderate", "Minor", "Unknown"])
predefined_certainty = set(["Observed", "Likely", "Possible", "Unlikely", "Unknown"])
predefined_certainty_severity = predefined_severity | predefined_certainty


def make_list_of_valid_files(filebase,schemas):
    """Compiles an index file containing information about each of the CAP
        files that start with the given filebase, writing the index file to the
        directory containing the files."""

    files = []
    filesearch = "{0}*.cap.xml".format(filebase)
    filenames = glob.glob(filesearch)
    filenames.sort()
    
    # Load the CAP schema.
    schema_doc = etree.parse(os.path.join(schemas, "CAP-v1.2.xsd"))
    schema = etree.XMLSchema(schema_doc)


    capalerts={}
    references = {}

    for fname in filenames:
        
        # Parse and validate each CAP file found.
        root = etree.parse(fname)
        nsmap = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}
        
        if schema.validate(root):
            
            attributes = {}

            # capalert is a dictionary with all the info needed to publish one cap
            capalert = {}
            capalert['identifier'] = root.find('.//cap:identifier', nsmap).text
            capalert['filename'] = os.path.basename(fname)
            capalert['msgType'] = root.find('.//cap:msgType', nsmap).text
            if capalert['msgType'] != 'Alert':
                capalert['references']=[]
                for original_id in publishcap.find_references(root, ""):
                    capalert['references'].append(original_id)
                references[capalert['identifier']]= capalert['references']
            capalert['sent'] =   root.find('.//cap:sent', nsmap).text
            capalert['capinfos'] = []


            for info in root.findall('cap:info', nsmap):
                capinfo={}
                capinfo['language'] =  info.find('cap:language', nsmap).text
                vf = info.find('cap:onset', nsmap).text
                vt = info.find('cap:expires', nsmap).text
                capinfo['onset'] = vf
                capinfo['expires'] = vt
                area = info.find('cap:area', nsmap)
                capinfo['areaDesc']= area.find('cap:areaDesc', nsmap).text
                capinfo['description'] = info.find('cap:description', nsmap).text
                for eventCode in info.findall('cap:eventCode', nsmap):
                    valueName= eventCode.find('cap:valueName',nsmap).text
                    value = eventCode.find('cap:value',nsmap).text
                    capinfo[valueName]=value
                # This headline should be common for all info elements
                capinfo['headline'] = info.find('cap:headline', nsmap).text
                valid_from = dateutil.parser.parse(vf)
                valid_to = dateutil.parser.parse(vt)
                attributes["valid_from"] = valid_from.strftime("%Y-%m-%dT%H:%M:%SZ")
                attributes["valid_to"] = valid_to.strftime("%Y-%m-%dT%H:%M:%SZ")
                capalert['capinfos'].append(capinfo)
            # Append the file name and validity of each validated CAP file to the list
            # that will be used to compile the index.
            files.append((fname, attributes))

            capalerts[capalert['identifier']]= capalert


        else:
            sys.stderr.write("Warning: CAP file '%s' is not valid.\n" % fname)

    make_index_file(filebase, files)
    update_references(capalerts,references)

    cap_no_list = make_cap_list("no",capalerts)
    cap_en_list = make_cap_list("en",capalerts)

    dirname = os.path.dirname(filebase)
    write_json(cap_no_list, dirname, "CAP_no.json")
    write_json(cap_en_list, dirname, "CAP_en.json")


def make_cap_list(language, capalerts):
    caplist = []
    for identifier, capalert in capalerts.iteritems():
        cap_entry = {}
        cap_entry['id'] = capalert['identifier']
        cap_entry['file'] = capalert['filename']
        if 'ref_by' in capalert:
            cap_entry['ref_by'] = capalert['ref_by']
        else:
            cap_entry['ref_by'] = None
        cap_entry['type'] = capalert['msgType']
        if 'references' in capalert:
            cap_entry['ref_to'] = capalert['references']
        else:
            cap_entry['ref_to'] = None
        cap_entry['t_published'] = capalert['sent']
        cap_entry['title'] = u""
        cap_entry['area'] = u""
        cap_entry['t_onset'] = u""
        cap_entry['t_expires'] = u""
        cap_entry['description'] = u"<b>MSGTYPE:</b> %s <br /></br>" %(capalert['msgType'])

        for info in capalert['capinfos']:
            if info['language'] == language:
                cap_entry['title'] = info['headline']
                if cap_entry['area']:
                    cap_entry['area']+= ", "
                cap_entry['area'] += info['areaDesc']
                #TODO use earliest/latest time for all infos to calculate onset/expires
                cap_entry['t_onset']= info['onset']
                cap_entry['t_expires'] = info['expires']
                cap_entry['description'] += make_description(info)

        caplist.append(cap_entry)
    return caplist

def make_description(info):

    if info['language'] == 'no':
        desc = u"""<b>%s</b><br /><table>
        <tr><th align='left'>Område:</th><td>%s</td></tr>
        <tr><th align='left' valign='top'>Varsel:</th><td> %s </td>
        <tr><th align='left'>Gyldighetstid:</th><td>Fra %s  til %s</td></tr></tr>
        </table><br />"""
    else:
        desc = u"""<b>%s</b><br /><table>
        <tr><th align='left'>Area:</th><td>%s</td></tr>
        <tr><th align='left' valign='top'>Forecast:</th><td> %s </td>
        <tr><th align='left'>Valid time:</th><td>From %s to %s</td></tr></tr>
        </table><br />"""


    if "event_level_name" in info:
        subtitle = info['event_level_name']
    else:
        subtitle = u""

    vfrom = dateutil.parser.parse(info['onset'])
    vto = dateutil.parser.parse(info['expires'])
    vfrom = vfrom.strftime("%Y-%m-%d %H:%M UTC")
    vto = vto.strftime("%Y-%m-%d %H:%M UTC")
    return desc % (subtitle, info['areaDesc'],info['description'],vfrom,vto)


def write_json(capalerts, dirname,filename):
    filename = os.path.join(dirname,filename)
    jason_cap = json.dumps(capalerts, sort_keys=True, ensure_ascii=False, indent=4, separators=(',', ': '))
    jsonfile = open(filename, "w")
    jsonfile.write(jason_cap.encode('utf-8'))
    jsonfile.close()


def update_references(capalerts,references):

    for key,value in references.iteritems():
        for id in value:
            
            if (id in capalerts):
                capalert=capalerts[id]
                capalert['ref_by']=key
            else:
                print("Could not find",id)



def make_index_file(filebase, files):
    # Produce the XML index file.
    root = Element('files', nsmap={'xsi': "http://www.w3.org/2001/XMLSchema-instance"})
    root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation", "mifare-index.xsd")
    for filename, valid in files:
        child = SubElement(root, 'file', valid)
        child.text = os.path.split(filename)[1]
    listfilename = "{0}-index.xml".format(filebase)
    listfile = open(listfilename, "w")
    listfile.write(tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True))
    listfile.close()




def get_urgency(date_from, date_to, now):
    """Finds the urgency based on the period, beginning at date_from and
    ending at date_to, and the current date, now."""

    # Sanity check the period times.
    if date_from > date_to:
        return "Unknown"

    # If we are already in the forecast period, the urgency is Immediate.
    if date_from <= now <= date_to:
        return "Immediate"

    # Check for a period in the past.
    if date_to <= now:
        return "Past"

    # The period is in the future.
    s = (date_from - now).total_seconds()

    if s < 3600:
        return "Expected"
    else:
        return "Future"

def make_awareness_level( sev ):
    """ Returns MeteoAlarm awareness-level based on severity """
    
    levels = {'min': "1; green; Minor",
              'mod': "2; yellow; Moderate",
              'sev': "3; orange; Severe",
              'ext': "4; red; Extreme"}
    
    lev = sev[:3].lower()
    
    try:
        ret = levels[lev]
    except:
        print "WRONG SEVERITY TO make_awarness_level. RETURNING DEFAULT VALUE"
        ret = "2; yellow; Moderate"
        
    return ret
    
def make_awareness_type( typ ):
    """ Returns MeteoAlarm awareness-type based on warning type
     """
    
    # The types are defined in the TED template and are therefore used unchanged
    
    types = {'Wind': "1; Wind",
             'snow-ice': "2; snow-ice",
             'Thunderstorm': "3; Thunderstorm",
             'Fog': "4; Fog",
             'high-temperature':"5; high-temperature",
             'low-temperature':"6; low-temperature",
             'coastalevent':"7; coastalevent",
             'forest-fire':"8; forest-fire",
             'avalanches':"9; avalanches",
             'Rain':"10; Rain",
             'flooding':"12; flooding",
             'rain-flood':"13; rain-flood",
             'Polar-low':"14; Polar-low"}
    
    try:
        ret = types[typ]
    except:
        print "WRONG TYPE ( %s ) TO make_awarness_TYPE. RETURNING DEFAULT VALUE, WIND" % typ
        ret = "1; Wind"
        
    return ret
    
    
    
def generate_file_cap_fare(filename, xmldoc, now, db):
    """Obtains the locations from the XML document given by xmldoc and the
    database, db, and writes a CAP file with the given filename.

    Structure:

        ALERT
            |
            | ----  Norwegian   --  INFO
            |                        |
            |                        | -- one or more -- RESOURCE
            |                        |
            |                        | -- one or more -- AREA
            |                        |
            |                    end INFO
            |
            | ----  English     --  INFO
            |                        |
            |                        | -- one or more -- RESOURCE
            |                        |
            |                        | -- one or more -- AREA
            |                        |
            |                    end INFO
            |
        end ALERT"""

    res = retrieve_from_xml_fare(xmldoc)
    numAreas = 0
    
    senders = {"no": "Meteorologisk Institutt",
               "nb": "Meteorologisk Institutt",
               "nn": "Meteorologisk Institutt",
               "en": "MET Norway"}
	
    sender = "noreply@met.no"
    identifier_prefix= "2.49.0.1.578.0.NO."
 

    notes = { "no":u'Varsel for "%s" for Norge utstedt av Meteorologisk Institutt. Melding nummer %s.',
               "nb":u'Varsel for "%s" for Norge utstedt av Meteorologisk Institutt. Melding nummer %s.',
               "nn":u'Varsel for "%s" for Norge utstedt av Meteorologisk Institutt. Melding nummer %s.',
               "en":u'%s alert for Norway issued by MET Norway. Message number %s.'}

    event_types = { "Wind": u"Vind",
                    "snow-ice" : u"Snø-Is",
                    "Thunderstorm" : u"Tordenbyger",
                    "Fog" : u"Tåke",
                    "high-temperature" : u"Høye temperaturer",
                    "low-temperature" : u"Lave temperaturer",
                    "coastalevent" : u"Hendelse på kysten",
                    "forest-fire" : u"Skogsbrann",
                    "avalanches"  : u"Skred",
                    "Rain" : u"Store nedbørsmengder",
                    "flooding" : u"Flom",
                    "rain-flooding" : u"Flom fra regn",
                    "Polar-low" : u"Polart lavtrykk"}

    l_type = res['type']
    l_alert = res['alert']
    
    # Check for values we absolutely need and set suitable defaults.
    
    language = "no"   #Suitable default. 
	
    if l_alert is None : 
       l_alert = "Alert"

    if l_type is None:
	    l_type = "Wind"


    alert = Element('alert')
    alert.set('xmlns', "urn:oasis:names:tc:emergency:cap:1.2")
    alert.addprevious(etree.ProcessingInstruction("xml-stylesheet", "href='capatomproduct.xsl' type='text/xsl'"))

    identifier = filter(lambda c: c.isalpha() or c.isdigit() or c in ["_","."], res['id'])

    sent_time = now.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    SubElement(alert, 'identifier').text = identifier_prefix + identifier
    SubElement(alert, 'sender').text =  sender
    SubElement(alert, 'sent').text = sent_time
    SubElement(alert, 'status').text = 'Test'
    SubElement(alert, 'msgType').text = l_alert
    SubElement(alert, 'scope').text = 'Public'
    
    # Optional element, although 'references' is mandatory for UPDATE and CANCEL.
    

    headline_no = get_headline(l_type,"no",sent_time, res['locations'])
    headline_en = get_headline(l_type,"en",sent_time,res['locations'])

    SubElement(alert, 'note').text = notes[language.split("-")[0]] % (l_type, res['mnr'])

    if l_alert != 'Alert':
        references = []
        for ref in filter(lambda ref: ref, res['references'].split(" ")):
            references.append(sender + "," + identifier_prefix + ref)
        SubElement(alert, 'references').text = " ".join(references)
    
    if res['eventname'] != None:
        SubElement(alert, 'incidents').text = res['eventname']
    
    dt = dateutil.parser.parse(res['vto'])
    df = dateutil.parser.parse(res['vfrom'])

    urgency = get_urgency(df, dt, now)

    for p in res['locations']:

        locs = res['locations'][p]

        severity = locs.get("severity", "Moderate")
        severity = severity.strip(invalid_extra_chars)
        severity = closest_match(severity, predefined_certainty_severity)

        certainty = locs.get("certainty", "Likely")
        certainty = certainty.strip(invalid_extra_chars)
        certainty = closest_match(certainty, predefined_certainty_severity)
        
        eng = locs['english']
        pict = locs['pictlink']
        infolink = locs['infolink']

        #################
        # NORWEGIAN INFO 
        #################

        language = "no"   #Suitable default.
        info = SubElement(alert, 'info')
        SubElement(info, 'language').text = language
        SubElement(info, 'category').text = 'Met'
        SubElement(info, 'event').text = event_types[l_type]
        SubElement(info, 'urgency').text = urgency
        SubElement(info, 'severity').text = severity
        SubElement(info, 'certainty').text = certainty

        # make eventCode with forecasters heading

        eventCode = SubElement(info,'eventCode')
        SubElement(eventCode,'valueName').text='event_level_name'
        SubElement(eventCode,'value').text =locs['heading']
        # Write UTC times to the CAP file.
        SubElement(info, 'effective').text = now.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        SubElement(info, 'onset').text = df.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        SubElement(info, 'expires').text = dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")

        SubElement(info, 'senderName').text = senders[language.split("-")[0]]
        SubElement(info, 'headline').text = headline_no

        SubElement(info, 'description').text = locs['varsel']
        SubElement(info, 'instruction').text = locs['instruction']
        SubElement(info, 'web').text = 'http://www.yr.no'

        # MeteoAlarm mandatory elements

        aw_level = SubElement( info, 'parameter')
        SubElement( aw_level, 'valueName' ).text = "awareness_level"
        SubElement( aw_level, 'value' ).text = make_awareness_level(severity)

        aw_type = SubElement( info , 'parameter')
        SubElement( aw_type , 'valueName' ).text = "awareness_type"
        SubElement( aw_type , 'value' ).text = make_awareness_type( l_type )

        # MET internal elements. Possibly used by Yr and others.

        met_trigger = SubElement( info, 'parameter' )
        SubElement( met_trigger, 'valueName' ).text = "trigger_level"
        SubElement( met_trigger, 'value' ).text = locs['triggerlevel']

        met_ret = SubElement( info, 'parameter' )
        SubElement( met_ret, 'valueName' ).text = "return_period"
        SubElement( met_ret, 'value' ).text = locs['retperiode']

        # Link to graphical representation
        
        if pict:
            resource = SubElement(info, 'resource')
            SubElement(resource, 'resourceDesc').text = "Grafiske beskrivelse av farevarslet"
            SubElement(resource, 'mimeType').text = "image/png"
            SubElement(resource, 'uri').text = pict

        # Link to further information
        
        if infolink:
            resource = SubElement(info, 'resource')
            SubElement(resource, 'resourceDesc').text = "Tilleggsinformasjon tilgjengelig fra andre"
            SubElement(resource, 'mimeType').text = "text/html"
            SubElement(resource, 'uri').text = infolink

        # Write multiple areas per info element,

        for n in locs['id'].split(":"):

            area = SubElement(info, 'area')
            SubElement(area, 'areaDesc').text = locs['name']

            altitude = locs['altitude']
            ceiling = locs['ceiling']

            latlon = get_latlon(n, db)
            if len(latlon) >= 3:

                # Optional polygon element with three unique points and the last
                # point identical to the first to close the polygon (at least
                # four points in total). Each point is specified by coordinates
                # of the form, latitude,longitude.
                polygon = SubElement(area, 'polygon')

                text = u''

                for name, lon, lat in latlon:
                    line = u"%f,%f\n" % (lat, lon)
                    text += line

                # Include the first point again to close the polygon.
                if latlon:
                    name, lon, lat = latlon[0]
                    text += u"%f,%f\n" % (lat, lon)

                polygon.text = text

                geocode = SubElement(area, 'geocode')
                SubElement(geocode, 'valueName').text = 'TED_ident'
                SubElement(geocode, 'value').text = locs['id']

                if altitude:
                	SubElement(area,'altitude').text = altitude
                	
                if ceiling:
                	SubElement(area,'ceiling').text = ceiling
                	           	
        #################
        # ENGLISH INFO 
        #################

        language = "en"
        info_en = SubElement(alert, 'info')
        SubElement(info_en, 'language').text = language
        SubElement(info_en, 'category').text = 'Met'
        SubElement(info_en, 'event').text = l_type
        SubElement(info_en, 'urgency').text = urgency
        SubElement(info_en, 'severity').text = severity
        SubElement(info_en, 'certainty').text = certainty

        eventCode_en = SubElement(info_en,'eventCode')
        SubElement(eventCode_en,'valueName').text='event_level_name'
        SubElement(eventCode_en,'value').text =locs['englishheading']
        # Write UTC times to the CAP file.
        SubElement(info_en, 'effective').text = now.strftime("%Y-%m-%dT%H:%M:00+00:00")
        SubElement(info_en, 'onset').text = df.strftime("%Y-%m-%dT%H:%M:00+00:00")
        SubElement(info_en, 'expires').text = dt.strftime("%Y-%m-%dT%H:%M:00+00:00")

        SubElement(info_en, 'senderName').text = senders[language.split("-")[0]]
        SubElement(info_en, 'headline').text = headline_en


        SubElement(info_en, 'description').text = locs['english']
        SubElement(info_en, 'instruction').text = locs['consequenses']
        SubElement(info_en, 'web').text = 'http://www.yr.no'

        # MeteoAlarm mandatory elements

        aw_level = SubElement( info_en, 'parameter')
        SubElement( aw_level, 'valueName' ).text = "awareness_level"
        SubElement( aw_level, 'value' ).text = make_awareness_level(severity)

        aw_type = SubElement( info_en , 'parameter')
        SubElement( aw_type , 'valueName' ).text = "awareness_type"
        SubElement( aw_type , 'value' ).text = make_awareness_type( l_type )

        # MET internal elements. Possibly used by Yr and others.

        met_trigger = SubElement( info_en, 'parameter' )
        SubElement( met_trigger, 'valueName' ).text = "trigger_level"
        SubElement( met_trigger, 'value' ).text = locs['triggerlevel']

        met_ret = SubElement( info_en, 'parameter' )
        SubElement( met_ret, 'valueName' ).text = "return_period"
        SubElement( met_ret, 'value' ).text = locs['retperiode']

        # Link to graphical representation
        
        if pict:
            resource = SubElement(info_en, 'resource')
            SubElement(resource, 'resourceDesc').text = "Graphical description of event"
            SubElement(resource, 'mimeType').text = "image/png"
            SubElement(resource, 'uri').text = pict

        # Link to further information
        
        if infolink:
            resource = SubElement(info_en, 'resource')
            SubElement(resource, 'resourceDesc').text = "Additional information available from others"
            SubElement(resource, 'mimeType').text = "text/html"
            SubElement(resource, 'uri').text = infolink

        # Write multiple areas per info element,

        for n in locs['id'].split(":"):

            area = SubElement(info_en, 'area')
            SubElement(area, 'areaDesc').text = locs['name']
            
            altitude = locs['altitude']
            ceiling = locs['ceiling']

            latlon = get_latlon(n, db)
            if len(latlon) >= 3:

                # Optional polygon element with three unique points and the last
                # point identical to the first to close the polygon (at least
                # four points in total). Each point is specified by coordinates
                # of the form, latitude,longitude.
                polygon = SubElement(area, 'polygon')

                text = u''

                for name, lon, lat in latlon:
                    line = u"%f,%f\n" % (lat, lon)
                    text += line

                # Include the first point again to close the polygon.
                if latlon:
                    name, lon, lat = latlon[0]
                    text += u"%f,%f\n" % (lat, lon)

                polygon.text = text

                geocode = SubElement(area, 'geocode')
                SubElement(geocode, 'valueName').text = 'TED_ident'
                SubElement(geocode, 'value').text = locs['id']
                
                if altitude:
                	SubElement(area,'altitude').text = altitude
                	
                if ceiling:
                	SubElement(area,'ceiling').text = ceiling
                	           	

        numAreas += 1

    # If no areas found, return without writing the file.
    if numAreas == 0:
        return

    f = open(filename, 'w')
    f.write(tostring(alert.getroottree(), encoding="UTF-8", xml_declaration=True,
                     pretty_print=True, standalone=True))
    f.close()


def get_headline(l_type,lang, sent, locations):

    notes = { "no":u'Varsel for %s for %s utstedt av Meteorologisk Institutt %s.',
               "en":u'%s alert for %s issued by MET Norway %s.'}

    event_types = { "Wind": u"Vind",
                    "snow-ice" : u"Snø-Is",
                    "Thunderstorm" : u"Tordenbyger",
                    "Fog" : u"Tåke",
                    "high-temperature" : u"Høye temperaturer",
                    "low-temperature" : u"Lave temperaturer",
                    "coastalevent" : u"Hendelse på kysten",
                    "forest-fire" : u"Skogsbrann",
                    "avalanches"  : u"Skred",
                    "Rain" : u"Store nedbørsmengder",
                    "flooding" : u"Flom",
                    "rain-flooding" : u"Flom fra regn",
                    "Polar-low" : u"Polart lavtrykk"}

    location_name = ""

    for locs in locations.values():
        #locs = locations[p]
        if location_name:
            location_name += ", "
        location_name += locs['name']



    if lang == "no":
        type = event_types[l_type].lower()
    else:
        type = l_type

    headline = notes[lang] % (type,location_name, sent)
    return headline


def generate_files_cap_fare(selectString, dateto, db, filebase,schemas):
    """Generates CAP files for the warnings obtained from the database, db,
    using the given selectString and dateto string. Writes an index file
    for the CAP files with names that begin with the given filebase string."""


    # TODO the function get_xml_docs should put all files on disk and then read them
    # termin can be found from the xml-tag productdescription (filename)
    docs = get_xml_docs(db, dateto, selectString)
    
    for doc in docs:

        tt=doc[1]
        ts = tt.strftime("%Y%m%dT%H%M%S")
        filename = filebase + "-" + ts + ".cap.xml"
        if (os.path.isfile(filename)): 
            sys.stderr.write("File '%s' already exists!\n" % filename)
        else:
            xmldoc=doc[0]
            sys.stderr.write("File '%s' will be generated\n" % filename)
            generate_file_cap_fare(filename, xmldoc, tt, db)

    make_list_of_valid_files(filebase,schemas)
