#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
"""Generates CAP alert."""

from fare_common import retrieve_from_xml_fare, get_latlon
from fare_setup import *
from lxml import etree
from lxml.etree import Element, SubElement
import dateutil.parser
import json

# global variables
event_types=[]
awareness_types={}
events={}


def read_json():
    global event_types
    global awareness_types
    global events
    with open("eventSeverityParameters.json", "r") as file:
        esp= file.read()

    eventSeverityParameters=json.loads(esp)
    event_types = eventSeverityParameters['eventTypes']
    awareness_types = eventSeverityParameters['awareness_types']
    events = eventSeverityParameters['eventNames']


def generate_capalert_v1(xmldoc,db):
    """Obtains the locations from the XML document given by xmldoc and the
    database, db, and returns a CAP alert.

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

    read_json()

    l_type = res['phenomenon_type']

    if res['forecasttype'] in ['gale','pl']:
        event_type = event_types_marine.get(l_type,event_type_default)
    else:
        event_type = event_types_land.get(l_type,event_type_default)

    l_alert = res['alert']
    termin = dateutil.parser.parse(res['termin'])

    alert = Element('alert')
    alert.set('xmlns', "urn:oasis:names:tc:emergency:cap:1.2")

    identifier = filter(lambda c: c.isalpha() or c.isdigit() or c in ["_","."], res['id'])

    sent_time = termin.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    SubElement(alert, 'identifier').text = identifier_prefix + identifier
    SubElement(alert, 'sender').text =  sender
    SubElement(alert, 'sent').text = sent_time
    SubElement(alert, 'status').text = res.get('status','Alert')
    SubElement(alert, 'msgType').text = l_alert
    SubElement(alert, 'scope').text = 'Public'

    # Optional element, although 'references' is mandatory for UPDATE and CANCEL.

#TODO set correct event_type
    #eventSeverityName=
    headline_no = get_headline( event_type,"no",sent_time, res['locations'])
    headline_en = get_headline(event_type,"en-GB",sent_time,res['locations'])

    # Insert CAP-version number
    SubElement(alert, 'code').text = "CAP-V12.NO.V1.0"

    if l_alert != 'Alert':
        references = []
        for ref in filter(lambda ref: ref, res['references'].split(" ")):
            references.append(sender + "," + identifier_prefix + ref)
        SubElement(alert, 'references').text = " ".join(references)



    if res.get('phenomenon_number'):
        SubElement(alert, 'incidents').text = incidents


    for loc in res['locations']:
        make_info_v1(alert, db, headline_no, event_type, loc, res, senders,"no")
        make_info_v1(alert, db, headline_en, event_type, loc, res, senders,"en-GB")

    return etree.tostring(alert.getroottree(), encoding="UTF-8", xml_declaration=True,
                     pretty_print=True, standalone=True)



def make_info_v1(alert, db, headline, event_type, loc, res, senders, language):

    onset = dateutil.parser.parse(loc['vfrom'])
    expires = dateutil.parser.parse(loc['vto'])
    effective = dateutil.parser.parse(loc['effective'])

    urgency = "Future"
    severity = loc.get("severity", "").strip()
    certainty = loc.get("certainty", "").strip()
    pict = loc['picturelink']
    infolink = loc['infolink']

    info = SubElement(alert, 'info')
    SubElement(info, 'language').text = language
    SubElement(info, 'category').text = 'Met'
    SubElement(info, 'event').text = events[event_type][language]
    SubElement(info, 'urgency').text = urgency
    SubElement(info, 'severity').text = severity
    SubElement(info, 'certainty').text = certainty

    eventCode = SubElement(info, 'eventCode')
    SubElement(eventCode, 'valueName').text = "eventType"
    SubElement(eventCode, 'value').text = event_type

    # Write UTC times to the CAP file.
    SubElement(info, 'effective').text = effective.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    SubElement(info, 'onset').text = onset.strftime("%Y-%m-%dT%H:00:00+00:00")
    SubElement(info, 'expires').text = expires.strftime("%Y-%m-%dT%H:00:00+00:00")
    SubElement(info, 'senderName').text = senders[language]
    SubElement(info, 'headline').text = headline
    if language=="no":
        SubElement(info, 'description').text = loc.get('varsel')
        SubElement(info, 'instruction').text = loc.get('instruction')
    elif language.startswith("en"):
        SubElement(info, 'description').text = loc['englishforecast']
        SubElement(info, 'instruction').text = loc.get('consequenses')

    SubElement(info, 'web').text = "http://met.no/Meteorologi/A_varsle_varet/Varsling_av_farlig_var/"

    parameters = get_parameters(loc, language,res,event_type)
    for valueName, value in parameters.items():
        parameter = SubElement(info, 'parameter')
        SubElement(parameter, 'valueName').text = valueName
        SubElement(parameter, 'value').text = value

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

    area = SubElement(info, 'area')
    SubElement(area, 'areaDesc').text = loc['name']

    altitude = loc.get('altitude')
    ceiling = loc.get('ceiling')

    name, latlon = get_latlon(loc['id'], db)
    if len(latlon) >= 3:

        # Optional polygon element with three unique points and the last
        # point identical to the first to close the polygon (at least
        # four points in total). Each point is specified by coordinates
        # of the form, latitude,longitude.
        polygon = SubElement(area, 'polygon')

        text = u''

        for lon, lat in latlon:
            line = u"%f,%f\n" % (lat, lon)
            text += line

        # Include the first point again to close the polygon.
        if latlon:
            lon, lat = latlon[0]
            text += u"%f,%f\n" % (lat, lon)

        polygon.text = text


        if altitude:
            SubElement(area, 'altitude').text = altitude

        if ceiling:
            SubElement(area, 'ceiling').text = ceiling



def get_parameters(loc, lang,res,event_type):

    severity=loc['severity'].lower().strip()
    phenomenon_name = res.get('phenomenon_name')

    parameters={}

    if lang == "no":
        parameters["event_manual_header"] = loc['heading']
    else:
          parameters["event_manual_header"]  = loc['englishheading']
    parameters["event_level_response"]=\
            get_event_level_response(severity,phenomenon_name,lang)
    parameters["event_level_type"]= level_type[lang][severity]
    # MeteoAlarm mandatory elements
    parameters["awareness_level"]= make_awareness_level(severity)
    parameters["awareness_type"]= awareness_types.get(event_type,"")
    # MET internal elements. Possibly used by Yr and others.
    parameters["trigger_level"]=loc['triggerlevel']
    parameters["return_period"]= loc['returnperiod']
    parameters['event_message_number'] = res.get('mnr')
    if phenomenon_name:
        parameters["incident_name"]=phenomenon_name


    return parameters


def get_headline(type,lang, sent, locations):

    notes = { "no":u'Varsel for %s for %s utstedt av Meteorologisk Institutt %s.',
               "en-GB":u'%s alert for %s issued by MET Norway %s.',
                "en":u'%s alert for %s issued by MET Norway %s.'}

    location_name = ""

    for locs in locations:
        if location_name:
            location_name += ", "
        location_name += locs['name']


    headline = notes[lang] % (type,location_name, sent)
    return headline


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


def get_event_level_response(severity,phenomenon_name,lang):
    response = level_response[lang][severity]
    if (severity=="extreme" and phenomenon_name):
        if lang == "no":
            response = response%("et",phenomenon_name)
        else:
            response = response%(phenomenon_name)

    return response

def get_event_level_type(severity,lang):

    type = level_type[lang][severity]

    return type
