#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

languages = ["no", "en-GB"]

senders ={
        "no": "Meteorologisk Institutt",
        "en-GB": "MET Norway",
        }


contact={
        "no": "https://www.met.no/kontakt-oss",
        "en-GB": "https://www.met.no/en/contact-us",
}


sender = "noreply@met.no"
identifier_prefix= "2.49.0.1.578.0."
web = "https://www.met.no/vaer-og-klima/farevarsel-og-ekstremvaer"

instructions={
        "no":u"",
        "en-GB": u""
}

responseType = "Monitor"
urgency = "Future"

geographicDomain={
"wind":"land",
"snow":"land",
"blowingSnow":"land",
"drivingConditions": "land",
"thunder":"land",
"fog":"land",
"highTemperature":"land",
"lowTemperature":"land",
"stormSurge":"land",
"forestFire":"land",
"avalanches":"land",
"rain":"land",
"flooding":"land",
"rainFlood":"land",
"polarLow":None,
"gale":"marine",
"icing":"marine",
"uvRadiation": None,
"pollen": "land",
"airPollution": "land"
}


# mapping from ted id to administrative ids
ted2Geocode = {
"0601": {"iso 3166-2":"NO-01","county":"01:30"},  # Østfold, 30 is code for Viken from 2020
"0602": {"iso 3166-2":"NO-02","county":"02:30"},  # Akershus, 30 is code for Viken from 2020
"0603": {"iso 3166-2":"NO-03","county":"03"},     # Oslo
"0604": {"iso 3166-2":"NO-04","county":"04:34"},  # Hedmark, 34 is code for Innlandet from 2020
"0605": {"iso 3166-2":"NO-05","county":"05:34"},  # Oppland,, 34 is code for Innlandet from 2020
"0606": {"iso 3166-2":"NO-06","county":"06:30"},  # Buskerud, 30 is code for Viken from 2020
"0607": {"iso 3166-2":"NO-07","county":"07:38"},  # Vestfold, 38 is code for Telemark og Vestfold from 2020
"0608": {"iso 3166-2":"NO-08","county":"08:38"},  # Telemark, 38 is code for Telemark og Vestfold from 2020
"0609": {"iso 3166-2":"NO-09","county":"09:42"},  # Aust-Agder, 42 is code for Agder from 2020
"0610": {"iso 3166-2":"NO-10","county":"10:42"}, # Vest-Agder, 42 is code for Agder from 2020
"0611": {"iso 3166-2":"NO-11","county":"11"},    # Rogaland
"0612": {"iso 3166-2":"NO-12","county":"12:46"}, # Hordaland, 46 is code for Vestlandet from 2020
"0614": {"iso 3166-2":"NO-14","county":"14:46"}, # Sogn og Fjordane, 46 is code for Vestlandet from 2020
"0615": {"iso 3166-2":"NO-15","county":"15"},    # Møre og Romsdal
"0616": {"iso 3166-2":"NO-16","county":"16:50"}, # Sør-Trøndelag, 50 is new code for Trøndelag from 2018
"0617": {"iso 3166-2":"NO-17","county":"17:50"}, # Nord-Trøndelag, 50 is new code for Trøndelag from 2018
"0618": {"iso 3166-2":"NO-18","county":"18"},    # Nordland
"0619": {"iso 3166-2":"NO-19","county":"19:54"}, # Troms, 54 is code for Troms og Finnmark from 2020
"0620": {"iso 3166-2":"NO-20","county":"20:54"}, # Finnmark, , 54 is code for Troms og Finnmark from 2020
"9001": {"iso 3166-2":"NO-18","county":"18"},    # Helgeland
"9002": {"iso 3166-2":"NO-18","county":"18"},    # Saltfjellet
"9003": {"iso 3166-2":"NO-18","county":"18"},    # Salten
"9004": {"iso 3166-2":"NO-18","county":"18"},    # Lofoten
"9005": {"iso 3166-2":"NO-18","county":"18"},    # Ofoten
"9006": {"iso 3166-2":"NO-18","county":"18"},    # Vesterålen
"9007": {"iso 3166-2":"NO-19","county":"19:54"}, # Sør-Troms
"9008": {"iso 3166-2":"NO-19","county":"19:54"}, # Nord-Troms
"9009": {"iso 3166-2":"NO-20","county":"20:54"}, # Øst-Finnmark
"9010": {"iso 3166-2":"NO-20","county":"20:54"}, # Kyst- og fjordstrøkene i Vest-Finnmark
"9011": {"iso 3166-2":"NO-20","county":"20:54"}, # Finnmarksvidda
"9018": {"iso 3166-2":"NO-21","county":"21",},   # Nordenskiöld Land på Spitsbergen
# Fjellet i Sør-Norge berører fylkene
    # Sør-Trøndelag, Oppland, Hedmark, Buskerud,Telemark, Aust-Agder, Vest-Agder, Rogaland,Hordaland,
    # Sogn og Fjordane, Møre og Romsdal
"0710" : {"iso 3166-2":"NO-16:NO-05:NO-04:NO-06:NO-08:NO-09:NO-10:NO-11:NO-12:NO-14:NO-15",
          "county":"16:05:04:06:08:09:10:11:12:14:15:50:34:30:38:42:46",}
}
