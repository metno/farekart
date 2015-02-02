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
			<input type="submit" value="Hent data">
		    </form></body></html>
		  """)
	else:
		req.content_type = "text/plain"
		req.write("NOT A GET METHOD CALL\n")

def latest(req):
    req.content_type = "text/html"
    
    response = urllib2.urlopen("https://api.npolar.no/expedition/track/?q=&filter-code=N-ICE2015&sort=measured&limit=all&filter-measured=2015-02-01T00:00:00..&format=geojson")
    
    data = response.read()
    
    js = json.loads(data)

    num = len(js['features'])
    
    lines = """<!DOCTYPE html>
<html>
<head>
  <title>LANCE OBSERVATIONS</title>
</head>

<body>

  <h1>Observations from LANCE</h1>
  <table style="width:100%">
  <tr>
    <th> Observing time </th>
    <th> Wind Speed Mean (m/s) </th> 
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
    
    for n in range(num-1,1,-1):
   
        tid = js['features'][n]['properties']['measured']
        ff  = js['features'][n]['properties']['wind_speed_mean']
        dd  = js['features'][n]['properties']['wind_direction_mean']
        tt  = js['features'][n]['properties']['air_temperature']
        pp  = js['features'][n]['properties']['air_pressure']
        hum = js['features'][n]['properties']['humidity']
        dept= js['features'][n]['properties']['depth']
        lat = js['features'][n]['properties']['latitude']
        lon = js['features'][n]['properties']['longitude']
        
        lines = lines + "<tr><td> %s </td><td> %s </td><td> %s </td><td> %s </td><td> %s </td><td> %s </td><td> %s </td><td> %s </td><td> %s </td></tr>\n" %( tid,ff,dd,tt,pp,hum,dept,lat,lon)
        
    lines = lines + """
</table>
</body>

</html>
  """    
            
    return lines


