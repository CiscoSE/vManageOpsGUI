#!/usr/bin/python38
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

from flask import Flask, request, make_response, render_template, redirect, url_for, session
from markupsafe import Markup
from includes import *
from json2html import *
import json

app = Flask(__name__)
app.secret_key = 'any random string'

###########################################################################
#  Prompt user to set vManage settings
###########################################################################
@app.route('/')
def getsettings():
    vmanage = request.cookies.get('vmanage')
    userid = request.cookies.get('userid')
    password = request.cookies.get('password')
    if vmanage == None:
        vmanage = userid = password = 'not set'
    return render_template('getsettings.html', vmanage=vmanage, userid=userid, password=password, secret='*****'+password[-2:])

###########################################################################
#  Read and save settings
###########################################################################
@app.route('/savesettings')
def savesettings():

    resp = make_response(redirect(url_for('menu')))

    ### Save vManage settings in a cookie:
    for arg in request.args:
        resp.set_cookie(arg, request.args.get(arg), secure=True, httponly=True)

    return resp

###########################################################################
#  Main menu.  This screen also clears any leftover session variables
###########################################################################

@app.route('/menu')
def menu():

    ### Clear user session variables from previous tasks
    session.clear()
    try:
        vmanage = login()
    except:
        return Markup(f'''Error attempting to log in.  Make sure:<br>
                      <ul><li>vManage is reachable from this server.
                    <li>Your vManage IP or Name is correct (do not include "https://", etc.)
                    <li>Your credentials have API privileges</ul>
                    <a href="/">Edit vManage settings</a>''')
    devices = vmanage.get_request('system/device/vedges')
    vmanage.logout()
    #print(json.dumps(devices,indent=2))
    models='<option label="all">all</option>\n'
    for device in devices['data']:
        print(device['deviceModel'])
        if device['deviceModel'] not in models:
            models += f'<option label="{device["deviceModel"]}">{device["deviceModel"]}</option>\n'
    print(models)
    return render_template('menu.html', vmanage=request.cookies.get('vmanage'), models=Markup(models))

###########################################################################
#  List edges.  Takes parameters model and mode.
###########################################################################

@app.route('/listedges')
def listedges():

    model = request.args.get('model') or 'all'
    mode = request.args.get('mode') or 'all'

    vmanage = login()
    data = list_edges(vmanage, mode = mode, model = model)
    vmanage.logout()
    data.insert(0, ['UUID','Hostname', 'Model','Mode'])
    output = buildtable(data)

    return render_template('table.html', title='List Edges', instructions='List of all edge devices',
                           data=Markup(output))

###########################################################################
#  List templates.  Takes parameter model.
###########################################################################
@app.route('/listtemplates')
def listtemplates():

    model = request.args.get('model') or 'all'
    vmanage = login()
    data = list_templates(vmanage, model)
    vmanage.logout()
    data.insert(0, ['UUID','Name', 'Description','Device Type'])
    output = buildtable(data)

    return render_template('table.html', title='List Templates', instructions='List of all templates',
                           data=Markup(output))

###########################################################################
#  RMA Edge. Collects device to replace, new device, and template details
###########################################################################
@app.route('/rmaedge')
def rmaedge():

    model = request.args.get('model') or session['model']
    session['model'] = model
    ### List edges in vManage mode for user to select from
    ### If oldedge is already set move to the next step.
    try:
        oldedge = request.args.get('oldedge') or session['oldedge']
        session['oldedge'] = oldedge
    except:
        vmanage = login()
        data = list_edges(vmanage, mode='vmanage', model=model)
        data.insert(0, ['UUID', 'Hostname', 'Model', 'Mode'])
        output = buildtable(data, link='/rmaedge?oldedge=')
        vmanage.logout()
        return render_template('table.html', data=Markup(output), title='Pick Old Edge',
                               instructions=Markup('Select the Edge device to replace:<br><br>'))

    ### List edges in CLI mode for user to choose from.
    ### If replacement edge is already set, move to the next step.
    try:
        newedge = request.args.get('newedge') or session['newedge']
        session['newedge'] = newedge
    except:
        vmanage = login()
        model = vmanage.get_request(f'device/models/{oldedge}')['name']
        session['model'] = model
        data = list_edges(vmanage, mode='cli', model=model)
        data.insert(0, ['UUID', 'Hostname', 'Model', 'Mode'])
        output = buildtable(data, link='/rmaedge?newedge=')
        vmanage.logout()
        return render_template('table.html', data=Markup(output), title='Pick New Edge',
                               instructions=Markup('Select the replacement Edge:<br><br>'))

    #
    # Gather data and pass to the RMA confirmation page
    #

    vmanage = login()
    template = get_device_template_variables(vmanage, oldedge)
    session['template'] = template
    vmanage.logout()
    jtemplate = Markup(json2html.convert(template))
    return render_template('rmaconfirm.html',template=jtemplate, oldedge=oldedge, newedge=newedge)

###########################################################################
#  RMA Edge confirmation screen prompts for confirmation and executes exchange
###########################################################################
@app.route('/rmaconfirm')
def rmaconfirm():

    #
    ### Deletes oldedge, attaches template to newedge, returns job result
    #

    ### Invalidate Device Certificate
    vmanage = login()
    cert_status = set_certificate(vmanage, session['oldedge'], session['model'], 'invalid')
    output = '<b>Invalidate Certificate:</b><br>'
    output += str(cert_status)

    ### Delete old device
    delete_status = vmanage.delete_request(f'system/device/{session["oldedge"]}')
    output += '<br><b>Delete Edge:</b><br>'
    output += str(delete_status)

    ### Create template variables JSON object with new UUID
    template = session['template']
    template['device'][0]['csv-deviceId'] = session['newedge']
    payload = {"deviceTemplateList":[
        template
    ]
    }
    output += '<br><b>Build template payload</b><br>'
    output += (json.dumps(payload,indent=2))

    ### Attach template to new edge
    attach_job = vmanage.post_request('template/device/config/attachment', payload = payload)
    output += '<br><b>Attach Template:</b><br>'
    output += str(attach_job)
    output += action_status(vmanage, attach_job['id'])

    vmanage.logout()
    output += '<br><br><a href="/">Return to main menu</a>'
    return Markup(output)


###########################################################################
#  Edit edge.  Collects edge device, displays form with template values
###########################################################################
@app.route('/editedge')
def editedge():

    model = request.args.get('model') or session['model']
    session['model'] = model
    ### Build a table of edges for user to select from.
    ### If edge has already been set, move to next step.
    try:
        edge = request.args.get('edge') or session['edge']
        session['edge'] = edge
    except:
        vmanage = login()
        data = list_edges(vmanage, mode='vmanage', model=model)
        data.insert(0, ['UUID', 'Hostname', 'Model', 'Mode'])
        output = buildtable(data, link='/editedge?edge=')
        vmanage.logout()
        return render_template('table.html', data=Markup(output), title='Edit Edge Values',
                               instructions=Markup('Select the Edge device to edit:<br><br>'))


    ### Build a form of template variables for user to edit.
    ### Uses templateId parameter or finds attached templateId
    ### Post form to update template
    vmanage = login()
    try:
        templateId = request.args.get('templateId') or session['templateId']
        template = get_device_template_variables(vmanage, edge, templateId)
    except:
        template = get_device_template_variables(vmanage, edge)
    vmanage.logout()
    session['template'] = template
    data = template['device'][0]
    tabdata = [['Field', 'Value']]
    formdata = {}
    for item in data:
        if item[0] == '/':
            formdata[item] = data[item]
        else:
            tabdata.append([item, data[item]])
    output = buildtable(tabdata)
    output += buildform(formdata, action='/updatetemp')
    return render_template('table.html', data=Markup(output), title='Edit Edge Values',
                           instructions=Markup('Edit any values below and submit to update the device configuration:<br><br>'))

###########################################################################
#  Attach template and monitor job result
###########################################################################
@app.route('/updatetemp', methods=['POST'])
def updatetemp():

    ### Retrieve variables and modify template
    template = session['template']
    output = '<A HREF="/menu">Return to Main Menu.</A><BR>'
    output += 'Old Template:<BR>' + json2html.convert(template)

    ### Create template variables JSON object with new UUID
    variables = request.form
    for value in variables:
        template['device'][0][value] = variables[value]
    payload = {"deviceTemplateList":[
        template
    ]
    }
    output += "<BR>New Template:<BR>" + json2html.convert(payload)

    ### Attach template to new edge
    vmanage = login()
    attach_job = vmanage.post_request('template/device/config/attachment', payload = payload)
    output += '<br><b>Attach Template:</b><br>'
    output += str(attach_job)
    output += action_status(vmanage, attach_job['id'])
    vmanage.logout()

    output += '<br><br><a href="/menu">Return to main menu</a>'

    return Markup(output)


###########################################################################
#  Deploy new edge. Prompt for edge, prompt for template, hand off to edit edge
###########################################################################
@app.route('/deployedge')
def deployedge():

    ### List edges in CLI mode for user to choose from.
    ### If replacement edge is already set, move to the next step.
    model = request.args.get('model') or session['model']
    session['model'] = model
    try:
        edge = request.args.get('edge') or session['edge']
        session['edge'] = edge
    except:
        vmanage = login()
        data = list_edges(vmanage, mode='cli', model=model)
        data.insert(0, ['UUID', 'Hostname', 'Model', 'Mode'])
        for edge in data:
            edgelink = f'<a href="/deployedge?edge={edge[0]}&model={edge[2]}">{edge[0]}</a>'
            edge[0] = edgelink
        output = buildtable(data)
        vmanage.logout()
        return render_template('table.html', data=Markup(output), title='Pick New Edge',
                               instructions=Markup('Select the replacement Edge:<br><br>'))

    ### Build a list of templates that apply to the edge deviceType for the user to choose from
    ### Send the templateId and deviceId to the Edit Edge routine
    vmanage = login()
    data = list_templates(vmanage, model=session['model'])
    vmanage.logout()
    data.insert(0, ['uuid', 'Name', 'Description', 'device type'])
    output = buildtable(data, link='/editedge?templateId=')
    return render_template('table.html', data=Markup(output), title='Pick a template', instructions=Markup('Select the template to apply:<br><br>'))

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python38_app]