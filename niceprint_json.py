#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# Author:  Bård Fjukstad
#
# Script for nice printing of json content using JSON module dumps function for content formatting.
#


import sys
import json


def read_json( filename):
    """ Read content of a json file """

    fil = open( filename , 'r')
    data = json.load( fil )
    fil.close()
    return data

def nice_print( data ):
    """Nice print json data"""

    str = json.dumps( data, sort_keys=True, indent=4, separators=(',', ': ') )
    print str

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "Usage:  python niceprint_json.py <json filename>"
        sys.exit(1)


    filename = sys.argv[1]

    data = read_json( filename )

    nice_print( data )


