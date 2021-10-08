#!/usr/bin/env python3
"""
Copyright (c) 2012 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""
__author__ = "David Brown <davibrow@cisco.com>"
__contributors__ = []
__copyright__ = "Copyright (c) 2012 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"

import json
from flask import request
from vmanage_api import rest_api_lib
from time import sleep

def login():

    ### Gets vManage variables from cookie and returns a vManage login object
    vmanage_name = request.cookies.get('vmanage')
    vmanage_user = request.cookies.get('userid')
    vmanage_pass = request.cookies.get('password')
    vmanage = rest_api_lib(vmanage_name, vmanage_user, vmanage_pass)

    return vmanage

def buildtable(data, link=False):

    ###  Builds an HTML table from data (list of lists)
    ###  Assumes row 0 are headers
    ###  If a link is passed, hyperlinks the first column by appending the string in
    ###  the first element of each row to the link string
    output = '<TABLE BORDER=1>\n'
    for header in data[0]:
        output += f'<TH ALIGN=left>{header}</TH>'
    start = 1 if link else 0
    for row in data[1:]:
        output += '\n<TR>'
        if link:
            output += f"<TD><A HREF='{link}{row[0]}'>{row[0]}</A>"
        for element in row[start:]:
            output += f"<TD>{element}</TD>"
        if link:
            output += f"</A>"
        output += '</TR>'
    output += '\n</TABLE>'
    return output

def buildform(data, action='/'):

    ###  Builds an HTML form from data (dict)
    output = f'<FORM ACTION={action} METHOD="post">\n'
    output +='<TABLE>'
    for item in data:
        output += f'<TR><TD><LABEL FOR="{item}">{item}</LABEL></TD>'
        output += f'<TD><INPUT TYPE="text" ID="{item}" NAME="{item}" VALUE="{data[item]}"></TD></TR>\n'
    output += '</TABLE><BR>\n<input type="submit" value="Submit">\n</FORM>'
    return output

def list_edges(vmanage, mode = 'all', model = 'all'):

    ### Returns a list of Edges as list of lists [uuid, deviceModel, configOperationMode]
    ### Set mode to all, cli, or vmanage
    response = vmanage.get_request('system/device/vedges')
    num = 1
    deviceList = []
    for device in response['data']:
        if mode=='all' or device['configOperationMode']==mode:
            if model == 'all' or device['deviceModel'] == model:
                try:
                    hostname = device['host-name']
                except:
                    hostname = 'UNASSIGNED'
                num += 1
                deviceList.append([device['uuid'], hostname, device['deviceModel'],device['configOperationMode']])
    return deviceList

def list_templates(vmanage, model = 'all'):

    ### Returns a list of templates as list of lists [uuid, Name, Description, device type]
    response = vmanage.get_request('template/device')['data']
    templatelist = []
    for template in response:
        if (template['deviceType'] == model) or (model == 'all'):
            templatelist.append([template['templateId'],template['templateName'],template['templateDescription'], template['deviceType']])
    return templatelist

def get_device_template_variables(vmanage, deviceId, templateId=None):

    ### Builds the JSON object that defines the template for a device
    ### Uses the templateId specified or finds and uses the attached templateId
    if not templateId:
        response = vmanage.get_request(f'system/device/vedge?uuid={deviceId}')
        templateId = response['data'][0]['templateId']
    payload = {"templateId": f"{templateId}", "deviceIds": [f"{deviceId}"], "isEdited": "false",
          "isMasterEdited": "false"}
    templateVariables = vmanage.post_request('template/device/config/input', payload)['data'][0]
    template = {
        "templateId": f"{templateId}",
        "device": [
            templateVariables
        ],
        "isEdited": False,
        "isMasterEdited": False
    }
    return template

def set_certificate(vmanage, uuid, model, state):

    ### Set device certificate state to valid, invalid or staging
    ### Find existing certificate details for device UUID
    ### Create certificate request payload JSON
    certrecords = vmanage.get_request(f'certificate/vedge/list?model={model}')['data']
    for device in certrecords:
        if device['uuid']==uuid:
            break
    payload = [
        {
        "serialNumber": f"{device['serialNumber']}",
        "chasisNumber": f"{uuid}",
        "validity": f"{state}"
        }
    ]

    cert_status = vmanage.post_request('certificate/save/vedge/list', payload)
    output = "<b>Set certificate state result:</b><br>" + json.dumps(cert_status, indent=2)

    cert_status = vmanage.post_request('certificate/vedge/list', payload='')
    output += "<br><b>Push certificate state to controllers result:</b><br>" + str(json.dumps(cert_status, indent=2))
    output += action_status(vmanage, cert_status['id'])

    return output

def action_status(vmanage, id):

    ### Monitors a job status every 5 seconds and returns the result
    output = '<br><b>Monitor Job Status:</b></br>'
    while (1):
        status = vmanage.get_request(f"device/action/status/{id}")
        status_res = status['summary']
        output += '<br>' + str(status_res)
        if status_res['status'] == "done":
            if ('Success' in status_res['count']) or ('Done - Scheduled' in status_res['count']):
                return output
            elif 'Failure' in status_res['count']:
                return "<br>" + str(status['data'][0]['activity']) + "<br>Failed"
        sleep(5)