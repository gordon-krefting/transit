import os.path
import requests
import untangle

response = requests.get('http://web.mta.info/status/ServiceStatusSubway.xml')

res = untangle.parse(response.text)

timestamp = res.Siri.ServiceDelivery.ResponseTimestamp.cdata

print(timestamp)

filename = 'rollingdata/status-{}.xml'.format(timestamp)

if (os.path.isfile(filename)):
    print('No update')
else:
    print('Updating...')
    with open(filename, 'w') as f:
        f.write(response.text)
