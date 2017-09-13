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
identifier_prefix= "2.49.0.1.578.0.NO."
web = "https://www.met.no/vaer-og-klima/farevarsel-og-ekstremvaer"

instructions={
        "no":u"Vurder behov for forebyggende tiltak. Beredskapsaktører skal vurdere fortløpende behov for beredskap.",
        "en-GB": u"Consider the need for preventive measures. Emergency Operators should consider ongoing need for preparedness. "
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
