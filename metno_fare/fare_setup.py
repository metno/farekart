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
"0601": {"iso 3166-2":"NO-01"},  # Østfold
"0602": {"iso 3166-2":"NO-02" }, # Akershus
"0603": {"iso 3166-2":"NO-03"},  # Oslo
"0604": {"iso 3166-2":"NO-04"},  # Hedmark
"0605": {"iso 3166-2":"NO-05" }, # Oppland
"0606": {"iso 3166-2":"NO-06"},  # Buskerud
"0607": {"iso 3166-2":"NO-07"},  # Vestfold
"0608": {"iso 3166-2":"NO-08" }, # Telemark
"0610": {"iso 3166-2":"NO-10"} , # Vest-Agder
"0611": {"iso 3166-2":"NO-11" }, # Rogaland
"0612": {"iso 3166-2":"NO-12" }, # Hordaland
"0614": {"iso 3166-2":"NO-14"},  # Sogn og Fjordane
"0615": {"iso 3166-2":"NO-15"},  # Møre og Romsdal
"0616": {"iso 3166-2":"NO-16"},  # Sør-Trøndelag
"0617": {"iso 3166-2":"NO-17"},  # Nord-Trøndelag
"0618": {"iso 3166-2":"NO-18"},  # Nordland
"0619": {"iso 3166-2":"NO-19"},  # Troms
"0620": {"iso 3166-2":"NO-20"},  # Finnmark
"9001": {"iso 3166-2":"NO-18"},  # Helgeland
"9002": {"iso 3166-2":"NO-18"},  # Saltfjellet
"9003": {"iso 3166-2":"NO-18"},  # Salten
"9004": {"iso 3166-2":"NO-18"},  # Lofoten
"9005": {"iso 3166-2":"NO-18"},  # Ofoten
"9006": {"iso 3166-2":"NO-18"},  # Vesterålen
"9007": {"iso 3166-2":"NO-19"},  # Sør-Troms
"9008": {"iso 3166-2":"NO-19"},  # Nord-Troms
"9009": {"iso 3166-2":"NO-20"},  # Øst-Finnmark
"9010": {"iso 3166-2":"NO-20"},  # Kyst- og fjordstrøkene i Vest-Finnmark
"9011": {"iso 3166-2":"NO-20"},  # Finnmarksvidda
# Fjellet i Sør-Norge berører fylkene
# Sør-Trøndelag, Oppland, Hedmark, Buskerud,Telemark, Aust-Agder, Vest-Agder, Hordaland,
# Sogn og Fjordane, Møre og Romsdal
"0710" : {"iso 3166-2":"NO-16:NO-05:NO-04:NO-06:NO-08:NO-09:NO-10:NO-12:NO-14:NO-15"}
}