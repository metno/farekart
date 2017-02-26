#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

senders ={
        "no": "Meteorologisk Institutt",
        "en-GB": "MET Norway",
        "en": "MET Norway",
        }

sender = "noreply@met.no"
identifier_prefix= "2.49.0.1.578.0.NO."


event_types = {
        "Wind": u"Vind",
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
         "Polar-low" : u"Polart lavtrykk"
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

# awareness_type used in Meteoalarm
awareness_types = {
    'Wind': "1; Wind",
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
    'Polar-low':"14; Polar-low"
}

