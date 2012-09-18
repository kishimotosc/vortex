import sys
import urllib, urllib2
import json

url = 'http://localhost:9000/'

if sys.argv[1] == 'save':
    url += 'v_save'
    func = 'set'
    parameter = [sys.argv[4], sys.argv[5]]
elif sys.argv[1] == 'load':
    url += 'v_load'
    func = 'get'
    parameter = [sys.argv[4]]
elif sys.argv[1] == 'delete':
    url+ = 'v_delete'
    func = ''
    parameter = [None]
else:
    sys.exit()

arguments = {
    'v_user'     : 'user1',
    'v_workspace': 'my_work',
    'v_document' : 'my_doc',
    'v_key'      : sys.argv[3],
    'v_function' : func,
    'v_parameter': json.dumps(parameter),
    'v_version'  : sys.argv[2],
    'v_limit'    : '3.0',
    'v_sleep'    : '0.5',
}

arguments_url_encoded = urllib.urlencode(arguments, True)
response_encoded = urllib2.urlopen(url, arguments_url_encoded).read()
response = json.loads(response_encoded)
if len(response) == 3:
    flag, all_ok, responses = response
    print flag, all_ok
else:
    flag, all_ok, responses, value, version = response
    print flag, all_ok, value, version
for response in responses:
    if len(response) == 3:
        location, flag, message = response
    else:
        location, flag, message, value, version = response
    print '----'
    print location
    print flag
    print message
    if len(response) != 3:
        print value, version
print '---- ---- ---- ----'
