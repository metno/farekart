#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from distutils.core import setup

setup(
    name="python-farekart",
    description="Generate kml and cap-files from text warnings in Ted database",
    author="Bård Fjukstad",
    author_email="b.fjukstad@met.no",
    url="http://www.met.no/",
    version="0.1.0",
    py_modules=["generatecap","fare_utilities"],
    scripts=["faremeldinger.py"]
    )
