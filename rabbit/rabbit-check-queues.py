#!/usr/bin/env python
"""
Check rabbit for queues older than <time>
Usage:
  rabbit-check-queues.py (-e host) [-h] [-d] [-p port] [-t time]
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

arguments = docopt(__doc__, version='Check Rabbit Queues 1.0')

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

queue_url = "http://" + host + ":" + port + "/api/queues/%2F/"
response = requests.get(queue_url, auth=HTTPBasicAuth(user, password))

queues = response.json()

def delete_queue(queue_name):
  url = queue_url + queue_name
  response = requests.delete(queue_url, auth=HTTPBasicAuth(user, password))
  print "Responose: %s" % response

def check_idle_time(idle_since, queue_name, idle_delta=86400):
  delta_time = datetime.datetime.now() - datetime.timedelta(seconds=idle_delta)
  # 2015-07-31 16:51:04
  idle_time = datetime.datetime.strptime(idle_since, "%Y-%m-%d %H:%M:%S")
  if delta_time > idle_time:
    print "We've been idle more than a day, and have no consumers; deleting queue %s" % queue_name
    return True

for queue in queues:
  if "consumers" in queue and queue['consumers'] == 0:
    if "idle_since" in queue and "auto_delete" in queue and queue['auto_delete'] and check_idle_time(queue['idle_since'], queue['name'], time_delta) and do_delete:
      print "Name: %s" % queue['name']
      print "Idle Since: %s" % queue['idle_since']
      print "Auto Delete: %s" % queue['auto_delete']
      print "Consumers: %s" % queue['consumers']
      delete_queue(queue['name'])
      print ""

print "There are %s queues" % len(queues)
