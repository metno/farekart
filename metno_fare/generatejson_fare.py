#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
"""Generates Json file with a list of all CAP files on disk."""

import glob
import json
import datetime
import os
import sys
from lxml import etree
import dateutil.parser
import linecache

nsmap = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}
MAX_WEEKS_TO_KEEP = 4

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    return 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)


def make_list_of_valid_files(filebase,schemas):
    """Compiles a Json file containing information about each of the CAP
        files that start with the given filebase, writing the Json file to the
        directory containing the files."""

    filesearch = "{0}*.cap.xml".format(filebase)
    filenames = glob.glob(filesearch)
    filenames.sort()

    # Load the CAP schema.
    schema_doc = etree.parse(os.path.join(schemas, "CAP-v1.2.xsd"))
    schema = etree.XMLSchema(schema_doc)

    capalerts={}
    references = {}

    for fname in filenames:

        # Parse and validate each CAP file found.
        root = etree.parse(fname)

        if schema.validate(root):

            # capalert is a dictionary with all the info needed to publish one cap
            capalert = {}
            capalert['identifier'] = root.find('.//cap:identifier', nsmap).text
            capalert['filename'] = os.path.basename(fname)
            capalert['msgType'] = root.find('.//cap:msgType', nsmap).text
            if capalert['msgType'] != 'Alert':
                capalert['references']=[]
                for original_id in find_references(root):
                    capalert['references'].append(original_id)
                references[capalert['identifier']]= capalert['references']
            capalert['sent'] =   root.find('.//cap:sent', nsmap).text
            capalert['capinfos'] = []


            for info in root.findall('cap:info', nsmap):
                capinfo={}
                capinfo['language'] =  info.find('cap:language', nsmap).text
                capinfo['severity'] =  info.find('cap:severity', nsmap).text
                capinfo['county'] =  list()
                vf = info.find('cap:onset', nsmap).text
                vt = info.find('cap:expires', nsmap).text
                capinfo['onset'] = vf
                capinfo['expires'] = vt
                area = info.find('cap:area', nsmap)
                capinfo['areaDesc']= area.find('cap:areaDesc', nsmap).text
                for geocode in area.findall('cap:geocode', nsmap):
                    try:
                        valueName = geocode.find('cap:valueName', nsmap).text
                        value = geocode.find('cap:value', nsmap).text
                        if valueName == 'county':
                            capinfo['county'].append(value)
                    except Exception as inst:
                        sys.stderr.write("Could not get county geocode from CAP file %s,%s : %s %s \n" % (valueName,value,PrintException(), inst.message))
                capinfo['description'] = info.find('cap:description', nsmap).text
                for eventCode in info.findall('cap:eventCode', nsmap):
                    valueName= eventCode.find('cap:valueName',nsmap).text
                    value = eventCode.find('cap:value',nsmap).text
                    capinfo[valueName]=value
                for parameter in info.findall('cap:parameter', nsmap):
                    valueName = parameter.find('cap:valueName', nsmap).text
                    value = parameter.find('cap:value', nsmap).text
                    capinfo[valueName] = value



                # This headline should be common for all info elements
                capinfo['headline'] = info.find('cap:headline', nsmap).text
                capalert['capinfos'].append(capinfo)

            capalerts[capalert['identifier']]= capalert


        else:
            sys.stderr.write("Warning: CAP file '%s' is not valid.\n" % fname)

    update_references(capalerts,references)

    cap_no_list = make_cap_list("no",capalerts,write_counties=True)
    cap_en_list = make_cap_list("en-GB",capalerts,write_counties=True)

    dirname = os.path.dirname(filebase)
    write_json(cap_no_list, dirname, "CAP_no.json")
    write_json(cap_en_list, dirname, "CAP_en.json")

    # make Json list for testing with counties
    cap_no_test_list = make_cap_list("no",capalerts,write_counties=True)
    cap_en_test_list = make_cap_list("en-GB",capalerts,write_counties=True)
    write_json(cap_no_test_list, dirname, "test_CAP_no.json")
    write_json(cap_en_test_list, dirname, "test_CAP_en.json")



def find_references(cap):
    """Finds the references in a CAP document, cap, and yields each identifier
    in turn."""

    references = cap.find('.//cap:references', nsmap).text.strip().split()
    references = filter(lambda word: word, references)
    for ref in references:

        pieces = ref.split(",")
        if len(pieces) != 3:
            sys.stderr.write("Error: CAP file '%s' contains invalid cancellation references.\n" % file_name)
            sys.exit(1)

        sender, original_id, time = pieces
        yield original_id


def make_cap_list(language, capalerts,write_counties=False):
    now = datetime.datetime.now(dateutil.tz.tzutc())
    caplist = []
    for identifier, capalert in capalerts.iteritems():
        expires_list = []
        onset_list= []
        is_extreme=False

        cap_entry = {}
        cap_entry['id'] = capalert['identifier']
        cap_entry['file'] = capalert['filename']
        if 'ref_by' in capalert:
            cap_entry['ref_by'] = capalert['ref_by']
        else:
            cap_entry['ref_by'] = None
        cap_entry['type'] = capalert['msgType']
        if 'references' in capalert:
            cap_entry['ref_to'] = capalert['references']
        else:
            cap_entry['ref_to'] = None
        cap_entry['t_published'] = capalert['sent']
        cap_entry['title'] = u""
        cap_entry['area'] = u""
        cap_entry['t_onset'] = u""
        cap_entry['t_expires'] = u""
        cap_entry['description'] = capalert['msgType']

        for info in capalert['capinfos']:
            if info['language'] == language:
                cap_entry['title'] = info['headline']  # all infos have the same headline
                if cap_entry['area']:
                    cap_entry['area']+= ", "
                cap_entry['area'] += info['areaDesc']
                if info['severity']=='Extreme':
                    is_extreme = True
                expires_list.append(dateutil.parser.parse(info['expires']))
                onset_list.append(dateutil.parser.parse(info['onset']))

                cap_entry['description'] = "%s: %s" % (cap_entry['description'],make_description(info))
                if 'eventType' in info:
                    cap_entry['event']=info['eventType']
                if 'geographicDomain' in info:
                    cap_entry['geographicDomain']=info['geographicDomain']
                if write_counties and 'county' in info:
                    cap_entry['county']=info['county']



        if (onset_list):
            onset = min(onset_list)
            cap_entry['t_onset'] = onset.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        if (expires_list):
            expires = max(expires_list)
            cap_entry['t_expires'] = expires.strftime("%Y-%m-%dT%H:%M:%S+00:00")

        # keep entries for MAX_WEEKS_TO_KEEP
        # keep all exteme warnings
        if (is_extreme or now-expires < datetime.timedelta(weeks=MAX_WEEKS_TO_KEEP)):
            caplist.append(cap_entry)


    return sorted(caplist,key=lambda caplist: caplist['t_published'],reverse=True)


def make_description(info):

    return info['description']

    if info['language'] == 'no':
        desc = u"""<b>%s</b><br /><table>
        <tr><th align='left'>Område:</th><td>%s</td></tr>
        <tr><th align='left' valign='top'>Varsel:</th><td> %s </td>
        <tr><th align='left'>Gyldighetstid:</th><td>Fra %s  til %s</td></tr></tr>
        </table><br />"""
    else:
        desc = u"""<b>%s</b><br /><table>
        <tr><th align='left'>Area:</th><td>%s</td></tr>
        <tr><th align='left' valign='top'>Forecast:</th><td> %s </td>
        <tr><th align='left'>Valid time:</th><td>From %s to %s</td></tr></tr>
        </table><br />"""


    if "event_level_name" in info:
        # old version
        subtitle = info['event_level_name']
    elif "eventAwarenessName" in info:
        #version v1
        subtitle = info['eventAwarenessName']
    else:
        subtitle = u""

    vfrom = dateutil.parser.parse(info['onset'])
    vto = dateutil.parser.parse(info['expires'])
    vfrom = vfrom.strftime("%Y-%m-%d %H:%M UTC")
    vto = vto.strftime("%Y-%m-%d %H:%M UTC")
    return desc % (subtitle, info['areaDesc'],info['description'],vfrom,vto)


def write_json(capalerts, dirname,filename):
    filename = os.path.join(dirname,filename)
    jason_cap = json.dumps(capalerts, sort_keys=True, ensure_ascii=False, indent=4, separators=(',', ': '))
    jsonfile = open(filename, "w")
    jsonfile.write(jason_cap.encode('utf-8'))
    jsonfile.close()


def update_references(capalerts,references):

    for key,value in references.iteritems():
        for id in value:

            if (id in capalerts):
                capalert=capalerts[id]
                capalert['ref_by']=key
            else:
                print("Could not find",id)
