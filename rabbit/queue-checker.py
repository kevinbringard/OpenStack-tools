#!/usr/bin/env python

import json
import commands
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--password", help="Password to auth against the rabbit server")
parser.add_argument("--user", help="Username to auth against the rabbit server")
parser.add_argument("--host", help="The hostname to get queue information from", default="127.0.0.1")
parser.add_argument("--vhost", help="The rabbit vhost to get queue information for", default="/")
parser.add_argument("--consumers", help="Comsumers threshold to alert on", default=0)
parser.add_argument("--messages", help="Messages threshold to alert on", default=10)
args = parser.parse_args()

command = "./rabbitadmin.py --host", args.host, "--vhost", args.vhost, "--username", args.user, "--password", args.password, "-f raw_json list queues"
command = " ".join(command)

json_data = commands.getoutput(command)
data = json.loads(json_data)

for queue in data:
  name = queue['name']
  consumers = queue['consumers']
  messages = queue['messages']
  if consumers <= int(args.consumers) and messages >= int(args.messages):
    print "Queue:", name, "Consumers:", consumers, "Messages:", messages
