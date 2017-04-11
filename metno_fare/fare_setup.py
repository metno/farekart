#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

senders ={
        "no": "Meteorologisk Institutt",
        "en-GB": "MET Norway",
        "en": "MET Norway",
        }

sender = "noreply@met.no"
identifier_prefix= "2.49.0.1.578.0.NO."


#mapping from Meteoalarm event types in our template to our event types on land, migh be obsolete later
event_types_land = {
        "Wind": "wind",
        "snow-ice" : "drivingConditions",
        "Thunderstorm" : "thunder",
        "Fog" :"fog",
        "high-temperature" : "highTemperature",
        "low-temperature" : "lowTemperature",
        "coastalevent" : "stormSurge",
        "forest-fire" : "forestFire",
        "avalanches"  : "avalanches",
        "Rain" : "rain",
        "flooding" : "flooding",
        "rain-flooding" :"flashFlood",
        "Polar-low" : "polarLow"
    }


#mapping from Meteoalarm event types to our marine event types, migh be obsolete later
event_types_marine = {
        "Wind": "gale",
        "coastalevent" : "icing",
        "Polar-low" : "polarLow"
    }

event_type_default="dangerWarning"

event_level_name={
    "vind":{
        "moderate":" Kraftig vind",
        "severe": "Svært kraftig vind",
        "extreme": "Ekstrem vind"


    }

}

level_response ={
    "no": {
            'minor': "Ulempe",
            'moderate': u"Følg med",
            'severe': u"Vær forberedt",
            'extreme': u'Ekstremvær%s %s'},
    "en-GB": {
            'minor': "Inconvenience",
            'moderate': "Be aware",
            'severe': "Be prepared",
            'extreme': "Take action! Extreme weather %s"}
    }


level_type = {
    "no" :{
            'minor': "",
            'moderate': u"Utfordrende situasjon",
            'severe': u"Farlig situasjon",
            'extreme': u"Ekstrem situasjon"},
    "en-GB":{
            'minor': "",
            'moderate': "Challenging situation",
            'severe': "Dangerous situation",
            'extreme': "Extreme situation"}
    }

