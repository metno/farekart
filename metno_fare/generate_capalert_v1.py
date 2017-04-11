#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
"""Generates CAP alert."""

from fare_common import retrieve_from_xml_fare, get_latlon
from fare_setup import *
from lxml import etree
from lxml.etree import Element, SubElement
import dateutil.parser
import json
import locale

# global variables
event_types=[]
awareness_types={}
awareness_levels={}
events={}
severityResponse={}
severitySeriousness={}
eventSeverityName={}

class info:
    def __init__(self,lang,event_type,geographicDomain,phenomenon_name,loc,db):
        self.lang=lang
        self.event_type=event_type
        self.geographicDomain=geographicDomain
        self.phenomenon_name=phenomenon_name
        self.onset = dateutil.parser.parse(loc['vfrom'])
        self.expires = dateutil.parser.parse(loc['vto'])
        self.effective = dateutil.parser.parse(loc['effective'])
        self.urgency = "Future"
        self.severity = loc.get("severity", "").strip()
        self.certainty = loc.get("certainty", "").strip()
        self.pict = loc['picturelink']
        self.infolink = loc['infolink']
        self.event = events[event_type][lang]
        if event_type not in ['gale','forestFire']:
            self.eventEndingTime=self.expires
        else:
            self.eventEndingTime=None

        if (lang=="no"):
            self.eventManualHeader=loc['heading']
        else:
            self.eventManualHeader=loc['englishheading']

        self.triggerLevel=loc['triggerlevel']
        self.returnPeriod = loc['returnperiod']

        self.eventSeverityName=eventSeverityName[self.event_type][self.certainty][self.lang][self.severity]

        # TODO instructions are hardcoded  but should be in Json file
        if lang == "no":
            self.description = loc.get('varsel')
            self.consequences = loc.get('instruction')
            self.instruction = u"Vurder behov for forebyggende tiltak. Beredskapsakt�rer skal vurdere fortl�pende behov for beredskap"
        elif lang.startswith("en"):
            self.description = loc['englishforecast']
            self.consequences = loc.get('consequenses')
            self.instruction= u"Consider the need for preventive measures. Emergency Operators should consider ongoing need for preparedness "


    # info for the area element. One for each info
        self.areaDesc = loc['name']
        self.altitude = loc.get('altitude')
        self.ceiling = loc.get('ceiling')
        self.polygon=get_polygon(db, loc)

    def get_parameters(self):

        parameters={}

        parameters["eventManualHeader"]  = self.eventManualHeader
        parameters["severityResponse"]=\
                getSeverityResponse(self.severity,self.phenomenon_name,self.lang)
        parameters["severitySeriousness"]= severitySeriousness[self.lang][self.severity]

        # MeteoAlarm mandatory elements
        parameters["awareness_level"]= awareness_levels.get(self.severity,"")
        parameters["awareness_type"]= awareness_types.get(self.event_type,"")

        # MET internal elements. Possibly used by Yr and others.
        parameters["triggerLevel"]=self.triggerLevel
        parameters["returnPeriod"]= self.returnPeriod

        if self.phenomenon_name:
            parameters["incidentName"]=self.phenomenon_name

        parameters["geographicDomain"]=self.geographicDomain
        if (self.eventEndingTime):
            parameters["eventEndingTime"]=self.eventEndingTime.strftime("%Y-%m-%dT%H:00:00+00:00")

        parameters["consequences"] = self.consequences
        parameters["eventSeverityName"] = self.eventSeverityName


        return parameters

    def set_all_locations_name(self,locs):
        self.all_locations_name = get_all_locations_name(locs)

    def create_headline(self):
        self.headline = get_headline(self.eventSeverityName,self.lang,self.onset,self.expires,self.all_locations_name)

def read_json():
    global event_types
    global awareness_types
    global awareness_levels
    global events
    global severityResponse
    global severitySeriousness
    global eventSeverityName
    with open("eventSeverityParameters.json", "r") as file:
        esp= file.read()

    eventSeverityParameters=json.loads(esp)
    event_types = eventSeverityParameters['eventTypes']
    awareness_types = eventSeverityParameters['awareness_types']
    awareness_levels = eventSeverityParameters['awareness_levels']
    events = eventSeverityParameters['eventNames']
    severityResponse=eventSeverityParameters['severityResponse']
    severitySeriousness=eventSeverityParameters['severitySeriousness']
    eventSeverityName=eventSeverityParameters['eventSeverityName']

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


    # Insert CAP-version number
    SubElement(alert, 'code').text = "CAP-V12.NO.V1.0"

    # Optional element, although 'references' is mandatory for UPDATE and CANCEL.
    if l_alert != 'Alert':
        references = []
        for ref in filter(lambda ref: ref, res['references'].split(" ")):
            references.append(sender + "," + identifier_prefix + ref)
        SubElement(alert, 'references').text = " ".join(references)


    if res.get('phenomenon_number'):
        SubElement(alert, 'incidents').text = incidents

    # get information common for all info blocks
    event_type = get_event_type(res)
    geographicDomain=get_geographicDomain(res)
    phenomenon_name = res.get('phenomenon_name')


    languages = ["no", "en-GB"]
    for loc in res['locations']:
        for lang in languages:
            l_info = info(lang,event_type,geographicDomain,phenomenon_name,loc,db)
            l_info.set_all_locations_name(res['locations'])
            l_info.create_headline()

            make_info_element(alert ,l_info)

    return etree.tostring(alert.getroottree(), encoding="UTF-8", xml_declaration=True,
                     pretty_print=True, standalone=True)


def get_geographicDomain(res):
    if res['forecasttype'] in ['gale', 'pl']:
        geographicDomain="marine"
    else:
        geographicDomain="land"
    return geographicDomain

def get_event_type(res):
    # mapping from Meteoalarm event types in our template to our event types on land, migh be obsolete later
    event_types_land = {
        "Wind": "wind",
        "snow-ice": "drivingConditions",
        "Thunderstorm": "thunder",
        "Fog": "fog",
        "high-temperature": "highTemperature",
        "low-temperature": "lowTemperature",
        "coastalevent": "stormSurge",
        "forest-fire": "forestFire",
        "avalanches": "avalanches",
        "Rain": "rain",
        "flooding": "flooding",
        "rain-flooding": "flashFlood",
        "Polar-low": "polarLow"
    }

    # mapping from Meteoalarm event types to our marine event types, migh be obsolete later
    event_types_marine = {
        "Wind": "gale",
        "coastalevent": "icing",
        "Polar-low": "polarLow"
    }

    event_type_default = "dangerWarning"

    l_type = res['phenomenon_type']
    if res['forecasttype'] in ['gale', 'pl']:
        event_type = event_types_marine.get(l_type, l_type)
    else:
        event_type = event_types_land.get(l_type, l_type)
    return event_type


def make_info_element(alert, l_info):

    info = SubElement(alert, 'info')
    SubElement(info, 'language').text = l_info.lang
    SubElement(info, 'category').text = 'Met'
    SubElement(info, 'event').text = l_info.event
    SubElement(info, 'urgency').text = l_info.urgency
    SubElement(info, 'severity').text = l_info.severity
    SubElement(info, 'certainty').text = l_info.certainty

    eventCode = SubElement(info, 'eventCode')
    SubElement(eventCode, 'valueName').text = "eventType"
    SubElement(eventCode, 'value').text = l_info.event_type

    # Write UTC times to the CAP file.
    SubElement(info, 'effective').text = l_info.effective.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    SubElement(info, 'onset').text = l_info.onset.strftime("%Y-%m-%dT%H:00:00+00:00")
    SubElement(info, 'expires').text = l_info.expires.strftime("%Y-%m-%dT%H:00:00+00:00")
    SubElement(info, 'senderName').text = senders[l_info.lang]
    SubElement(info, 'headline').text = l_info.headline
    SubElement(info, 'description').text = l_info.description
    SubElement(info, 'instruction').text = l_info.instruction
    SubElement(info, 'web').text = "http://met.no/Meteorologi/A_varsle_varet/Varsling_av_farlig_var/"

    parameters = l_info.get_parameters()
    for valueName, value in parameters.items():
        parameter = SubElement(info, 'parameter')
        SubElement(parameter, 'valueName').text = valueName
        SubElement(parameter, 'value').text = value

    # Link to graphical representation
    if l_info.pict:
        resource = SubElement(info, 'resource')
        SubElement(resource, 'resourceDesc').text = "Grafiske beskrivelse av farevarslet"
        SubElement(resource, 'mimeType').text = "image/png"
        SubElement(resource, 'uri').text = l_info.pict

    # Link to further information
    if l_info.infolink:
        resource = SubElement(info, 'resource')
        SubElement(resource, 'resourceDesc').text = "Tilleggsinformasjon tilgjengelig fra andre"
        SubElement(resource, 'mimeType').text = "text/html"
        SubElement(resource, 'uri').text = l_info.infolink

    area = SubElement(info, 'area')
    SubElement(area, 'areaDesc').text = l_info.areaDesc

    if (l_info.polygon):
        polygon = SubElement(area, 'polygon')
        polygon.text = l_info.polygon

    if l_info.altitude:
            SubElement(area, 'altitude').text = l_info.altitude

    if l_info.ceiling:
            SubElement(area, 'ceiling').text = l_info.ceiling


def get_polygon(db, loc):
    text = u''
    name, latlon = get_latlon(loc['id'], db)
    if len(latlon) >= 3:

        # Optional polygon element with three unique points and the last
        # point identical to the first to close the polygon (at least
        # four points in total). Each point is specified by coordinates
        # of the form, latitude,longitude.

        for lon, lat in latlon:
            line = u"%f,%f\n" % (lat, lon)
            text += line

        # Include the first point again to close the polygon.
        if latlon:
            lon, lat = latlon[0]
            text += u"%f,%f\n" % (lat, lon)

    return text

def get_headline(type,lang, onset, expires , all_locations_name):

    headline_templates = { "no":u'%s, %s ,%s til %s.',
               "en-GB":u'%s, %s .%s to %s.'}

    # sudo locale-gen nb_NO.utf8 if this does not work
    if (lang == "no"):
        locale.setlocale(locale.LC_ALL, "nb_NO.utf8")
    else:
        locale.setlocale(locale.LC_ALL, "en_GB.utf8")

    #vfrom = onset.strftime("%A %d %B %H:%M")
    #vto = expires.strftime("%A %d %B %H:%M")
    vfrom = onset.strftime("%d %B %H:%M")
    vto = expires.strftime("%d %B %H:%M")

    headline = headline_templates[lang] % (type,all_locations_name, vfrom,vto)

    return headline


def get_all_locations_name(locations):
    location_name = ""
    for locs in locations:
        if location_name:
            location_name += ", "
        location_name += locs['name']
    return location_name


def getSeverityResponse(severity,phenomenon_name,lang):
    response = severityResponse[lang][severity]
    if (severity=="extreme" and phenomenon_name):
        if lang == "no":
            response = response%("et",phenomenon_name)
        else:
            response = response%(phenomenon_name)

    return response