#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Setup an AMIV API for use with the amiv-checkin tool."""


from sys import argv
import requests

if len(argv) < 5:
    print("Usage: %s <API URL> <root password> <admin username> <admin password> <admin group name>" % argv[0])
    exit(1)

API_URL_c = str(argv[1])
rootpw_c = str(argv[2])
auth_obj = requests.auth.HTTPBasicAuth(rootpw_c, "")

ADMIN_BN_c = str(argv[3])
ADMIN_PW_c = str(argv[4])
ADMIN_GROUP_c = str(argv[5])


def api_delete(obj):
    delurl = API_URL_c + "/" + str(obj['_links']['self']['href'])
    headers = {'If-Match': obj['_etag']}
    r = requests.delete(delurl, headers=headers, auth=auth_obj)
    if r.status_code not in [200, 202, 204]:
        print('Error with API access: '+str(r.text))
        exit(1)

# create your checkin admin user
data = {
    'nethz': ADMIN_BN_c,
    'password': ADMIN_PW_c,
    'gender': 'male',
    'firstname': 'Checkin',
    'lastname': 'Admin',
    'membership': 'regular',
    'email': ADMIN_BN_c + '@amiv.ethz.ch'
}
r = requests.post(API_URL_c + '/users', json=data, auth=auth_obj)
if r.status_code is not 201:
    print('Error with API access: '+str(r.text))
    exit(1)
adminuser = r.json()

# create checkin admin group
data = {
  "name": ADMIN_GROUP_c,
  "requires_storage": False,
  "allow_self_enrollment": False,
  "moderator": str(adminuser['_id']),
  "permissions": {
        "events": "read",
        "users": "read",
        "eventsignups": "readwrite"
    }
}
r = requests.post(API_URL_c + '/groups', json=data, auth=auth_obj)
if r.status_code is not 201:
    print('Error with API access: '+str(r.text))
    api_delete(adminuser)
    exit(1)
admingroup = r.json()

# make adminuser member of admingroup
data = {
    "group": admingroup['_id'],
    "user": adminuser['_id']
}
r = requests.post(API_URL_c + '/groupmemberships', json=data, auth=auth_obj)
if r.status_code is not 201:
    print('Error with API access: '+str(r.text))
    api_delete(admingroup)
    api_delete(adminuser)
    exit(1)

# output to user
print("Generated Checkin Administrator user and group.")
print("Administrator username: '{:s}' password:'{:s}'".format(ADMIN_BN_c, ADMIN_PW_c))
print("Administrator group name: '{:s}' _id:'{:s}' <<-- copy this into config.py".format(ADMIN_GROUP_c, admingroup['_id']))
print("Setup succeeded.")
