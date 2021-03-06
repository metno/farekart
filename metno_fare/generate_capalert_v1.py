#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
"""Generates CAP alert."""
import dateutil.parser
from lxml import etree

from lxml.etree import Element, SubElement

from event_awareness_parameters import *
from fare_common import retrieve_from_xml_fare, get_latlon, translate_name
import fare_setup

class info:
    def __init__(self,lang,event_type,phenomenon_name,loc,db):
        self.lang=lang
        self.event_type=event_type
        self.geographicDomain = fare_setup.geographicDomain[event_type]
        self.phenomenon_name=phenomenon_name
        self.onset = dateutil.parser.parse(loc['vfrom'])
        self.expires = dateutil.parser.parse(loc['vto'])
        self.effective = dateutil.parser.parse(loc['effective'])
        self.responseType=fare_setup.responseType
        self.urgency = fare_setup.urgency
        self.severity = loc.get("severity", "").strip()
        self.certainty = loc.get("certainty", "").strip()
        self.pict = loc['picturelink']
        self.infolink = loc['infolink']
        self.areaDesc=""

        # dependencies of parameters on event_type, lang,certainty and severity handled in event_awareness_par
        self.event_awareness_par = event_awareness_parameters(event_type,lang,self.certainty,self.severity)

        self.event = self.event_awareness_par.events
        self.eventAwarenessName = self.event_awareness_par.eventAwarenessName
        self.awarenessHeadline = self.event_awareness_par.awarenessHeadline


        if not self.eventAwarenessName:
            # in case eventSeverityName is not set, just use the self.event
            self.eventAwarenessName = self.event
        if self.eventAwarenessName:
            self.eventAwarenessName = unicode(self.eventAwarenessName).capitalize()


        if 'eventEndingTime' in loc:
            if loc['eventEndingTime']=="Yes":
                self.eventEndingTime=self.expires
            else:
                self.eventEndingTime=None
        else:
            if event_type not in ['gale','forestFire']:
                self.eventEndingTime=self.expires
            else:
                self.eventEndingTime=None

        self.triggerLevel=loc['triggerlevel']
        self.returnPeriod = loc['returnperiod']



        if lang == "no":
            self.description = loc.get('varsel')
            # old METfare template
            self.consequences = loc.get('instruction')
            # new METfare template
            if "consequences_no" in loc:
                self.consequences=loc.get('consequences_no')
            self.instruction = loc.get('instructions_no','')
            if "location_name_no" in loc:
                self.areaDesc = loc.get("location_name_no")
        elif lang.startswith("en"):
            self.description = loc['englishforecast']
            # old METfare template
            self.consequences = loc.get('consequenses')
            if "consequences_en" in loc:
            # new METfare template
                self.consequences = loc.get('consequences_en')
            self.instruction = loc.get('instructions_en',"")
            if "location_name_en" in loc:
                self.areaDesc = loc.get("location_name_en")


        if self.instruction:
            self.instruction = " ".join((self.instruction,fare_setup.instructions[lang]))
            self.instruction=self.instruction.strip()
        else:
            self.instruction = fare_setup.instructions[lang]

    # info for the area element. One for each info
        if not self.areaDesc:
            self.areaDesc = translate_name(db,lang,loc['name'])
        self.altitude = loc.get('altitude')
        self.ceiling = loc.get('ceiling')
        self.polygon=get_polygon(db, loc)
        self.all_ids=loc.get('all_ids')

    def get_parameters(self):

        parameters={}

        parameters["awarenessResponse"]=self.event_awareness_par.awarenessResponse
        parameters["awarenessSeriousness"]= self.event_awareness_par.awarenessSeriousness

        # MeteoAlarm mandatory elements
        parameters["awareness_level"]= self.event_awareness_par.awareness_levels
        parameters["awareness_type"]= self.event_awareness_par.awareness_types

        # MET internal elements. Possibly used by Yr and others.
        parameters["triggerLevel"]=self.triggerLevel
        parameters["returnPeriod"]= self.returnPeriod

        if self.phenomenon_name:
            parameters["incidentName"]=self.phenomenon_name

        parameters["geographicDomain"]=self.geographicDomain
        if (self.eventEndingTime):
            parameters["eventEndingTime"]=self.eventEndingTime.strftime("%Y-%m-%dT%H:00:00+00:00")
        if (self.consequences):
            parameters["consequences"] = self.consequences
        if (self.eventAwarenessName):
            parameters["eventAwarenessName"] = self.eventAwarenessName


        return parameters

    def set_all_locations_name(self,all_locations_name):
        self.all_locations_name = all_locations_name

    def create_headline(self):
        self.headline = get_headline(self.eventAwarenessName, self.awarenessHeadline, self.phenomenon_name,
                                     self.lang, self.effective, self.expires, self.areaDesc)


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

    l_alert = res['alert']
    termin = dateutil.parser.parse(res['termin'])

    alert = Element('alert')
    alert.set('xmlns', "urn:oasis:names:tc:emergency:cap:1.2")

    identifier = filter(lambda c: c.isalpha() or c.isdigit() or c in ["_","."], res['id'])

    sent_time = termin.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    # get information common for all info blocks
    event_type = get_event_type(res)
    phenomenon_name = res.get('phenomenon_name')
    status="Actual"
    if phenomenon_name=="Test":
        status="Test"


    SubElement(alert, 'identifier').text = fare_setup.identifier_prefix + identifier
    SubElement(alert, 'sender').text =  fare_setup.sender
    SubElement(alert, 'sent').text = sent_time
    #SubElement(alert, 'status').text = res.get('status','Actual')
    SubElement(alert, 'status').text =  status
    SubElement(alert, 'msgType').text = l_alert
    SubElement(alert, 'scope').text = 'Public'


    # Insert CAP-version number
    SubElement(alert, 'code').text = "CAP-V12.NO.V1.0"

    # Optional element, although 'references' is mandatory for UPDATE and CANCEL.
    if l_alert != 'Alert':
        references = []
        for ref in filter(lambda ref: ref, res['references'].split(" ")):
            references.append(fare_setup.sender + "," + fare_setup.identifier_prefix + ref)
        SubElement(alert, 'references').text = " ".join(references)


    if res.get('phenomenon_number'):
        SubElement(alert, 'incidents').text=res['phenomenon_number']


    all_location_names={}
    for lang in fare_setup.languages:
        all_location_names[lang]=get_all_locations_name(db,lang,res['locations'])

    for loc in res['locations']:
        for lang in fare_setup.languages:
            l_info = info(lang,event_type,phenomenon_name,loc,db)
            l_info.set_all_locations_name(all_location_names[lang])
            l_info.create_headline()

            make_info_element(alert ,l_info)

    return etree.tostring(alert.getroottree(), encoding="UTF-8", xml_declaration=True,
                     pretty_print=True, standalone=True)


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
        "rain-flooding": "rainFlood",
        "Polar-low": "polarLow"
    }

    # mapping from Meteoalarm event types to our marine event types, migh be obsolete later
    event_types_marine = {
        "Wind": "gale",
        "coastalevent": "icing",
        "Polar-low": "polarLow"
    }


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
    SubElement(info,'responseType').text = l_info.responseType
    SubElement(info, 'urgency').text = l_info.urgency
    SubElement(info, 'severity').text = l_info.severity
    SubElement(info, 'certainty').text = l_info.certainty

    eventCode = SubElement(info, 'eventCode')
    SubElement(eventCode, 'valueName').text = "eventType"
    SubElement(eventCode, 'value').text = l_info.event_type

    # Write UTC times to the CAP file.
    SubElement(info, 'effective').text = l_info.effective.strftime("%Y-%m-%dT%H:00:00+00:00")
    SubElement(info, 'onset').text = l_info.onset.strftime("%Y-%m-%dT%H:00:00+00:00")
    SubElement(info, 'expires').text = l_info.expires.strftime("%Y-%m-%dT%H:00:00+00:00")
    SubElement(info, 'senderName').text = fare_setup.senders[l_info.lang]
    SubElement(info, 'headline').text = l_info.headline
    SubElement(info, 'description').text = l_info.description
    SubElement(info, 'instruction').text = l_info.instruction
    if l_info.infolink:
        SubElement(info, 'web').text = l_info.infolink
    SubElement(info, 'contact').text = fare_setup.contact[l_info.lang]

    parameters = l_info.get_parameters()
    for valueName, value in parameters.items():
        # do not use empty parameters
        if (value):
            parameter = SubElement(info, 'parameter')
            SubElement(parameter, 'valueName').text = valueName
            SubElement(parameter, 'value').text = value

    # Link to graphical representation
    if l_info.pict:
        resource = SubElement(info, 'resource')
        caption = fare_setup.caption[l_info.lang]
        if l_info.headline:
            caption = caption + l_info.headline[0].lower() + l_info.headline[1:]
        SubElement(resource, 'resourceDesc').text = caption
        SubElement(resource, 'mimeType').text = "image/png"
        SubElement(resource, 'uri').text = l_info.pict


    area = SubElement(info, 'area')
    SubElement(area, 'areaDesc').text = l_info.areaDesc

    if (l_info.polygon):
        polygon = SubElement(area, 'polygon')
        polygon.text = l_info.polygon


# get administrative geocodes from ted identifiers
    try:
        if l_info.all_ids:
                ted_ids=l_info.all_ids.split(":")
                geocodes={}
                for ted_id in ted_ids:
                    ted2Geo=fare_setup.ted2Geocode2020.get(ted_id)
                    if not ted2Geo:
                        continue
                    for code,ids in ted2Geo.items():
                        if code not in geocodes:
                            geocodes[code]=list()
                        for id in ids.split(":"):
                            if id not in geocodes[code]:
                                geocodes[code].append(id)
                for valueName,values in geocodes.items():
                    for value in values:
                        geocode=SubElement(area,'geocode')
                        SubElement(geocode, 'valueName').text = valueName
                        SubElement(geocode, 'value').text =value
    except Exception:
        print("Error creating geocode elements!")

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
            line = u"%f,%f " % (lat, lon)
            text += line

        # Include the first point again to close the polygon.
        if latlon:
            lon, lat = latlon[0]
            text += u"%f,%f\n" % (lat, lon)

    return text

def get_headline(type,awareness, incident_name,lang, effective, expires , all_locations_name):

    headline_templates = { "no":u'%s, %s, %s, %s UTC til %s UTC.',
               "en-GB":u'%s, %s, %s, %s UTC to %s UTC.'}

    # disable temporarily
    # sudo locale-gen nb_NO.utf8 if this does not work
    #if (lang == "no"):
    # locale.setlocale(locale.LC_ALL, "nb_NO.utf8")
    #else:
    #    locale.setlocale(locale.LC_ALL, "en_GB.utf8")

    #vfrom = onset.strftime("%A %d %B %H:%M")
    #vto = expires.strftime("%A %d %B %H:%M")
    vfrom = effective.strftime("%d %B %H:00")
    vto = expires.strftime("%d %B %H:00")

    headline = headline_templates[lang] % (type,awareness,all_locations_name, vfrom,vto)
    if (headline):
        headline=headline.strip()
        headline = headline[0].upper()+ headline[1:]


    if incident_name:
        extreme_name=""
        if lang == "no":
            extreme_name= u"Ekstremværet " + incident_name + ": "
        elif lang=="en-GB":
            extreme_name= "Extreme weather " + incident_name + ": "
        headline = extreme_name + headline



    return headline


def get_all_locations_name(db, lang,locations):
    location_name = ""
    for locs in locations:
        if location_name:
            location_name += ", "
        location_name += translate_name(db,lang,locs['name'])
    return location_name


