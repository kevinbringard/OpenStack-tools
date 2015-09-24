#!/usr/bin/env python
"""
Check rabbit for connections older than <time>

Usage:
  rabbit-check-connections.py (-e host) [-h] [-d] [-p port] [-t time]
                              (-u username)
                              (-x password)
                              [--version]

Options:
  -e <host>     Rabbit host to connect to
  -h, --help    Display this help message
  -d            Perform delete operation
  -p <port>     Port to connect to (defaults to 15672)
  -t <time>     Time to consider a queue stale in seconds (defaults to 86400; one day)
  -u <username> Rabbit username
  --version     Show version
  -x <password> Rabbit password
"""

import datetime
import requests
from docopt import docopt
from requests.auth import HTTPBasicAuth

arguments = docopt(__doc__, version='Check Rabbit Connections 1.0')

"""
{'--help': False,
 '--version': False,
 '-d': False,
 '-e': 'bob',
 '-p': '15672',
 '-u': 'foo',
 '-x': 'bar'}
"""

host = arguments.get('-e')
perform_delete = arguments.get('-d')
port = arguments.get('-p')
if port is None:
  port = "15672"

user = arguments.get('-u')
password = arguments.get('-x')
do_delete = arguments.get('-d')
time_delta = int(arguments.get('-t'))
if time_delta is None:
  time_delta = int(86400)

channel_url = "http://" + host + ":" + port + "/api/channels/"
connection_url = "http://" + host + ":" + port + "/api/connections/"
channel_response = requests.get(channel_url, auth=HTTPBasicAuth(user, password))
connection_response = requests.get(connection_url, auth=HTTPBasicAuth(user, password))

channel_data = channel_response.json()
connection_data = connection_response.json()

# Match up connections and channels and print
# Their data correlated

def delete_connection(connection_name):
  url = connection_url + connection_name
  response = requests.delete(url, auth=HTTPBasicAuth(user, password))
  print "We've been idle more than %s seconds, and have no consumers; deleting connection %s" % (time_delta, connection_name)
  print "Responose: %s" % response

def check_if_idle(idle_since, connection_name, idle_delta=86400):
  delta_time = datetime.datetime.now() - datetime.timedelta(seconds=idle_delta)
  # 2015-07-31 16:51:04
  idle_time = datetime.datetime.strptime(idle_since, "%Y-%m-%d %H:%M:%S")
  if delta_time > idle_time:
    return True
  else:
    return False

for connection in connection_data:
  if "peer_port" in connection:
    connection_peer_port = connection['peer_port']
  else:
    break
  for channel in channel_data:
    if "peer_port" in channel['connection_details']:
      channel_peer_port = channel['connection_details']['peer_port']
    else:
      break
    if connection_peer_port == channel_peer_port and "idle_since" in channel:
      if check_if_idle(channel['idle_since'], connection['name'], time_delta) and do_delete and channel['consumer_count'] == 0:
        delete_connection(connection['name'])
        
print "There are %s connections" % len(connection_data)
print "There are %s channels" % len(channel_data)
