#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu May 18 11:48:04 2017

@author: Maksym Dolgykh
"""

import sys
import argparse                                                                                                                                                                              
import requests                                                                                                                                                                              
                                                                                                                                                                                             
STATE_OK = 0                                                                                                                                                                                 
STATE_WARNING = 1                                                                                                                                                                            
STATE_CRITICAL = 2                                                                                                                                                                           
STATE_UNKNOWN = 3                                                                                                                                                                            
                                                                                                                                                                                             
                                                                                                                                                                                             
parser = argparse.ArgumentParser(description='Check OpenStack Ceilometer API for availability.')                                                                                                 
parser.add_argument('--auth_url', metavar='auth URL', type=str, required=True, help='Keystone URL')
parser.add_argument('--username', metavar='username', type=str, required=True, help='username to use for authentication')
parser.add_argument('--password', metavar='password', type=str, required=True, help='password to use for authentication')
parser.add_argument('--tenant', metavar='tenant', type=str, required=True, help='tenant name to use for authentication')
parser.add_argument('--region', metavar='region', type=str, required=False,
                    help='Name of the region as specified in the service catalog that this check needs to be run on.')
parser.add_argument('--req_count', metavar='numberMeters', type=int, default=1,
                    required=False, help='minimum number of meters in ceilometer required to pass the test')
parser.add_argument('--ceilometer_url', metavar='http://controller:8777', type=str, default='http://localhost:8777/v2',
                    required=False, help='Ceilometer endpoint to use, instead of the one returned by Keystone.')
parser.add_argument('--insecure', action='store_false', dest='verify',
                    required=False, help='Disable SSL verification.')
args = parser.parse_args()

headers = {'content-type': 'application/json'}

auth_token = None

ceilometer_url = None 

try:

    auth_request = '{"auth":{"tenantName": "' + args.tenant + '", "passwordCredentials": {"username": "' +  args.username + '", "password": "' + args.password + '"}}}'

    auth_response = requests.post(args.auth_url + '/tokens', data=auth_request, headers=headers, verify=args.verify).json();

    if not auth_response['access']['token']['id']:
        raise Exception("Authentication failed. Failed to get an auth token.")

    auth_token = auth_response['access']['token']['id']

    services = auth_response['access']['serviceCatalog']

    if args.ceilometer_url is None:
        for service in services:
            if service['type'] == 'metering':
                if args.region:
                    for region_urls in service['endpoints']:
                        if region_urls['region'] == args.region:
                            ceilometer_url = region_urls['publicURL']
                else:
                    ceilometer_url = service['endpoints'][0]['publicURL']
    else:
        ceilometer_url = args.ceilometer_url

    if ceilometer_url is None:
        raise Exception("Authentication succeeded but unable to find metering service")

except Exception as e:
    print('WARNING: Athentication failed for tenant %s and user %s' % (args.tenant, args.username))
    sys.exit(STATE_WARNING)

headers['X-Auth-Token'] = auth_token  

try:
    ceilometer_meters_list_response = requests.get(ceilometer_url + '/meters', headers=headers, verify=args.verify).json()
    meters_count = len(ceilometer_meters_list_response)
    if meters_count < args.req_count:
      print("CRITICAL: %d meters found less than required %d" % (meters_count, args.req_count))
      sys.exit(STATE_CRITICAL)

except Exception as e:
    print(e)
    print('CRITICAL: Failed to retrieve meters for tenant %s and user %s' % (args.tenant, args.username))
    sys.exit(STATE_CRITICAL)

print('OK: Retrived %d meters, required %d' % (meters_count, args.req_count))
sys.exit(STATE_OK)


