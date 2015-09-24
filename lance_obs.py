#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# Author:  Bård Fjukstad
#
# CGI script for requesting observations from LANCE and presenting these in a table.
#


from mod_python import apache
import tempfile
import os
import json
import urllib2



def index(req):
	req.content_type = "text/html"

	if req.method == "GET":
			req.write("""<html><body>
			<h1>Observations from LANCE</h1>
			<form action="lance_obs.py/latest" method="POST">
            <br>
            Data siden (mm/dd/yyyy): <input name="date" type="date" value="2015-02-01" min="2015-01-25">
            <br>
			<input type="submit" value="Hent data">
		    </form></body></html>
		  """)
	else:
		req.content_type = "text/plain"
		req.write("NOT A GET METHOD CALL\n")

def latest(req,date):
    req.content_type = "text/html"
    
    response = urllib2.urlopen("https://api.npolar.no/expedition/track/?q=&filter-code=N-ICE2015&sort=measured&limit=all&filter-measured=%sT00:00:00..&format=geojson" % date)
    
    data = response.read()
    
    js = json.loads(data)

    num = len(js['features'])
    
    lines = """<!DOCTYPE html>
<html>
<head>
  <title>LANCE OBSERVATIONS</title>
  <style>
    th { text-align: center; }
    td { text-align: center; }
  </style>
</head>

<body>

  <h1>Observations from LANCE</h1>
  <table style="width:100%">
  <tr>
    <th> Observing time </th>
    <th> Wind Speed Mean (knop) </th> 
    <th> Direction </th>
    <th> Air Temperature </th>
    <th> Air Pressure </th>
    <th> Humidity </th>
    <th> Depth </th>
    <th> Latitude </th>
    <th> Longitude </th>
  </tr>
  """

#    lines = lines + "Number of items : %d " % num  
#    lines = lines + str(js)
    
    for n in range(num-1,0,-1):
      try:   
        tid = js['features'][n]['properties']['measured']
      except:
        continue
      try:
        ff  = float( js['features'][n]['properties']['wind_speed_mean'] )
      except:
        ff = -1.0
      try:
        dd  = float( js['features'][n]['properties']['wind_direction_mean'] )
      except:
        dd = -1.0
      try:
        tt  = float( js['features'][n]['properties']['air_temperature'] )
      except:
        tt = -1.0
      try:
        pp  = float( js['features'][n]['properties']['air_pressure'] )
      except:
        pp = -1.0
      try:
        hum = float( js['features'][n]['properties']['humidity'] )
      except:
        hum = -1.0
      try:
        dept= float( js['features'][n]['properties']['depth'] )
      except:
        dept = -1.0
      try:
        lat = js['features'][n]['properties']['latitude']
      except:
        lat = -1.0
      try:
        lon = js['features'][n]['properties']['longitude']
      except:
        lon = -1.0
        
      lines = lines + "<tr><td> %s </td><td> %0.1f </td><td> %0.1f </td><td> %0.1f </td><td> %0.1f </td><td> %0.1f </td><td> %0.1f </td><td> %s </td><td> %s </td></tr>\n" %( tid,ff,dd,tt,pp,hum,dept,lat,lon)

    lines = lines + """
</table>
</body>

</html>
  """    
            
    return lines


