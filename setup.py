#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from distutils.core import setup

setup(
    name="python-farekart",
    description="Generate KML and CAP files from text warnings in the TED database",
    author="Bård Fjukstad",
    author_email="b.fjukstad@met.no",
    url="http://www.met.no/",
    version="0.3.13",
    packages=["metno_fare"],
    scripts=["faremeldinger.py", "cap2kml.py"],
    data_files=[("share/xml/farekart", 
                 ["schemas/XMLSchema.xsd", "schemas/CAP-v1.2.xsd",
                  "xsl/capatomproduct.xsl", "xsl/dst_check.xsl"]),
                ("etc/farekart",["etc/eventSeverityParameters.json"])

                ]
    )
