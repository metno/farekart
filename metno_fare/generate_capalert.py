#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
"""Generates CAP alert."""

from fare_common import retrieve_from_xml_fare, get_latlon
from lxml import etree
from lxml.etree import Element, SubElement
import dateutil.parser

def generate_capalert_fare(xmldoc,db):
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


    senders = {"no": "Meteorologisk Institutt",
               "nb": "Meteorologisk Institutt",
               "nn": "Meteorologisk Institutt",
               "en": "MET Norway"}

    sender = "noreply@met.no"
    identifier_prefix= "2.49.0.1.578.0.NO."

    note =  "Message number %s"


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

    l_type = res['phenomenon_type']
    event_type = { "no": event_types[l_type], "en":l_type}


    l_alert = res['alert']
    termin = dateutil.parser.parse(res['termin'])

    alert = Element('alert')
    alert.set('xmlns', "urn:oasis:names:tc:emergency:cap:1.2")

    identifier = filter(lambda c: c.isalpha() or c.isdigit() or c in ["_","."], res['id'])

    sent_time = termin.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    SubElement(alert, 'identifier').text = identifier_prefix + identifier
    SubElement(alert, 'sender').text =  sender
    SubElement(alert, 'sent').text = sent_time
    SubElement(alert, 'status').text = res.get('status','Test')
    SubElement(alert, 'msgType').text = l_alert
    SubElement(alert, 'scope').text = 'Public'

    # Optional element, although 'references' is mandatory for UPDATE and CANCEL.

    headline_no = get_headline( event_type["no"].lower(),"no",sent_time, res['locations'])
    headline_en = get_headline(event_type["en"],"en",sent_time,res['locations'])

    SubElement(alert, 'code').text = "system_version 0.1"
    SubElement(alert, 'note').text = note % res['mnr']

    if l_alert != 'Alert':
        references = []
        for ref in filter(lambda ref: ref, res['references'].split(" ")):
            references.append(sender + "," + identifier_prefix + ref)
        SubElement(alert, 'references').text = " ".join(references)


    if res.get('phenomenon_number') and res.get('phenomenon_name'):
        incidents = " ".join([res.get('phenomenon_number'),res.get('phenomenon_name')])
    elif res.get('phenomenon_name'):
        incidents = res['phenomenon_name']
    elif res.get('phenomenon_number'):
        incidents = res['phenomenon_number']
    else:
        incidents=""

    if (incidents):
        SubElement(alert, 'incidents').text = incidents


    for locs in res['locations']:
        make_info(alert, db, headline_no, event_type, l_type, locs, res, senders,"no")
        make_info(alert, db, headline_en, event_type, l_type, locs, res, senders,"en")

    return etree.tostring(alert.getroottree(), encoding="UTF-8", xml_declaration=True,
                     pretty_print=True, standalone=True)


def make_info(alert, db, headline, event_type, l_type, locs, res, senders,language):

    onset = dateutil.parser.parse(locs['vfrom'])
    expires = dateutil.parser.parse(locs['vto'])
    effective = dateutil.parser.parse(locs['effective'])

    urgency = "Future"
    severity = locs.get("severity")
    certainty = locs.get("certainty")
    pict = locs['picturelink']
    infolink = locs['infolink']

    info = SubElement(alert, 'info')
    SubElement(info, 'language').text = language
    SubElement(info, 'category').text = 'Met'
    SubElement(info, 'event').text = event_type[language]
    SubElement(info, 'urgency').text = urgency
    SubElement(info, 'severity').text = severity
    SubElement(info, 'certainty').text = certainty
    # make eventCode with forecasters heading
    eventCodes = getEventCode(locs, language, event_type[language],res)
    for valueName, value in eventCodes.items():
        eventCode = SubElement(info, 'eventCode')
        SubElement(eventCode, 'valueName').text = valueName
        SubElement(eventCode, 'value').text = value

    # Write UTC times to the CAP file.
    SubElement(info, 'effective').text = effective.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    SubElement(info, 'onset').text = onset.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    SubElement(info, 'expires').text = expires.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    SubElement(info, 'senderName').text = senders[language]
    SubElement(info, 'headline').text = headline
    if language=="no":
        SubElement(info, 'description').text = locs.get('varsel')
        SubElement(info, 'instruction').text = locs.get('instruction')
    elif language == "en":
        SubElement(info, 'description').text = locs['englishforecast']
        SubElement(info, 'instruction').text = locs.get('consequenses')

    SubElement(info, 'web').text = "http://met.no/Meteorologi/A_varsle_varet/Varsling_av_farlig_var/"
    # MeteoAlarm mandatory elements
    aw_level = SubElement(info, 'parameter')
    SubElement(aw_level, 'valueName').text = "awareness_level"
    SubElement(aw_level, 'value').text = make_awareness_level(severity)
    aw_type = SubElement(info, 'parameter')
    SubElement(aw_type, 'valueName').text = "awareness_type"
    SubElement(aw_type, 'value').text = make_awareness_type(l_type)
    # MET internal elements. Possibly used by Yr and others.
    met_trigger = SubElement(info, 'parameter')
    SubElement(met_trigger, 'valueName').text = "trigger_level"
    SubElement(met_trigger, 'value').text = locs['triggerlevel']
    met_ret = SubElement(info, 'parameter')
    SubElement(met_ret, 'valueName').text = "return_period"
    SubElement(met_ret, 'value').text = locs['returnperiod']
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
    SubElement(area, 'areaDesc').text = locs['name']

    altitude = locs.get('altitude')
    ceiling = locs.get('ceiling')

    name, latlon = get_latlon(locs['id'], db)
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

        geocode = SubElement(area, 'geocode')
        SubElement(geocode, 'valueName').text = 'TED_ident'
        SubElement(geocode, 'value').text = locs['id']

        if altitude:
            SubElement(area, 'altitude').text = altitude

        if ceiling:
            SubElement(area, 'ceiling').text = ceiling


def getEventCode(locs,lang,type,res):



    level_id = {'min': "1",
              'mod': "2",
              'sev': "3",
              'ext': "4"}


    if lang == "no":
        level_name = locs['heading']
        level_concept = {'min': "",
                'mod': u"Vær oppmerksom",
                'sev': u"Vær forberedt",
                'ext': u"Ta affære"}
    else:
        level_name = locs['englishheading']
        level_concept = {'min': "",
                'mod': u"Be aware",
                'sev': "Be prepared",
                'ext': "Take action"}

    lev = locs['severity'][:3].lower()

    if lev not in ['min','mod','sev','ext']:
        lev = 'mod'

    eventCodes = {'event_level_name': level_name,
            'event_level_concept': level_concept[lev],
            'event_level_id': level_id[lev],
            'event_level_type': type,
            'event_background_description': res.get("background_description") ,
            'event_message_number': res.get('mnr')}


    return eventCodes


def get_headline(type,lang, sent, locations):

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