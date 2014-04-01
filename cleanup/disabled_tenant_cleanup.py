#!/usr/bin/env python

import MySQLdb as mdb
import sys
import os
import argparse
import simplejson as json
from novaclient.v1_1 import client as nova
from cinderclient import client as cinder
from neutronclient.neutron import client as neutron

# Please NOTE at this time this script does nothing more than print
# the resources

# Pull in the environment variables
username=os.environ['OS_USERNAME']
password=os.environ['OS_PASSWORD']
auth_url=os.environ['OS_AUTH_URL']
project_id=os.environ['OS_TENANT_NAME']
tenant_id=os.environ['OS_TENANT_NAME']
DESCRIPTION = "OpenStack Resource Cleanup Tool"
DB_USER="user"
DB_PASS="pass"
DB_HOST="db-host"

def parse_args():
  # ensure environment has necessary items to authenticate
  for key in ['OS_TENANT_NAME', 'OS_USERNAME', 'OS_PASSWORD',
              'OS_AUTH_URL']:
    if key not in os.environ.keys():
      print "Your environment is missing, \
          please source your OpenStack credentials"

  ap = argparse.ArgumentParser(description=DESCRIPTION)
  ap.add_argument('-d', '--delete', action='store_true',
                  default=False, help='Delete active resources')

  return ap.parse_args()

def delete_instances(instance_uuids):
  nova_client = nova.Client(username, password, project_id, auth_url)

  for row in instance_uuids:
    instance_uuid = row['uuid']
    print "Deleting instance: %s" % instance_uuid
#    nova_client.servers.delete(instance_uuid)

def delete_snapshots(snapshot_uuids):
  cinder_client = cinder.Client('1', username, password, project_id, auth_url)

  for row in snapshot_uuids:
    snapshot_uuid = row["id"]
#    cinder_client.snapshot.delete(snapshot_uuid)

def delete_volumes(volume_uuids):
  cinder_client = cinder.Client('1', username, password, project_id, auth_url)

  for row in volume_uuids:
    volume_uuid = row['id']
  #  cinder_client.volumes.delete()

def delete_ports(port_uuids):
  """
  # neutron_client = neutron.Client('2.0', auth_url, tenant_id, username, password)

  for row in port_uuids:
    port_uuid = row['id']
  # neutron_client.delete_port(port_uuid)

  # print neutron_client.list_networks()

  """

def print_output(field_type, uuid_field, name_field, rows):
  print "  %s:" % field_type
  for row in rows:
    uuid = row[uuid_field]
    if not name_field:
      name = ""
    else:
      name = row[name_field]
    print "    %s (%s)" % (uuid, name)

args = parse_args()

# You'll need to put your DB creds in here. You'll need

con = mdb.connect(DB_HOST, DB_USER, DB_PASS)

with con:
  cur = con.cursor(mdb.cursors.DictCursor)

  # cur.execute("select * from keystone.project where enabled = 0")
  cur.execute("select * from keystone.project where enabled = 1 limit 10")

  rows = cur.fetchall()

  if rows:
    for row in rows:
      tenant_id = row["id"]
      name = row["name"]
      print "Tenant: %s (%s)" % (tenant_id, name)

      # Instances
      cur.execute("select * from nova.instances where project_id = %s and deleted = 0 ;", (tenant_id))
      rows = cur.fetchall()
      if args.delete:
        delete_instances(rows)
      else:
        print_output("Instances", "uuid", "hostname", rows)

      # Routers
      cur.execute("select * from neutron.routers where tenant_id = %s ;", (tenant_id))
      rows = cur.fetchall()
      if args.delete:
        delete_routers(rows)
      else:
        print_output("Routers", "id", "name", rows)

      # Networks
      cur.execute("select * from neutron.networks where tenant_id = %s ;", (tenant_id))
      rows = cur.fetchall()
      if args.delete:
        delete_networks(rows)
      else:
        print_output("Networks", "id", "name", rows)

      # Subnets
      cur.execute("select * from neutron.subnets where tenant_id = %s ;", (tenant_id))
      rows = cur.fetchall()
      if args.delete:
        delete_subnets(rows)
      else:
        print_output("Subnets", "id", "name", rows)

      # Floating IPs
      cur.execute("select * from neutron.floatingips where tenant_id = %s ;", (tenant_id))
      rows = cur.fetchall()
      if args.delete:
        delete_floating_ips(rows)
      else:
        print_output("Floating IPs", "id", "floating_ip_address", rows)

      # Load balancers (pools)
      cur.execute("select * from neutron.pools where tenant_id = %s ;", (tenant_id))
      rows = cur.fetchall()
      if args.delete:
        delete_load_balancers(rows)
      else:
        print_output("Load Balancers", "id", "name", rows)

      # VIPs
      cur.execute("select * from neutron.vips where tenant_id = %s ;", (tenant_id))
      rows = cur.fetchall()
      if args.delete:
        delete_vips(rows)
      else:
        print_output("VIPs", "id", "name", rows)

      # Ports
      cur.execute("select * from neutron.ports where tenant_id = %s ;", (tenant_id))
      rows = cur.fetchall()
      if args.delete:
        delete_ports(rows)
      else:
        print_output("Ports", "id", "name", rows)

      # Snapshots
      cur.execute("select * from cinder.snapshots where project_id = %s and deleted = 0;", (tenant_id))
      rows = cur.fetchall()
      if args.delete:
        delete_snapshots(rows)
      else:
        print_output("Snapshots", "id", "", rows)

      # Volumes
      cur.execute("select * from cinder.volumes where project_id = %s and deleted = 0 ;", (tenant_id))
      rows = cur.fetchall()
      if args.delete:
        delete_volumes(rows)
      else:
        print_output("Volumes", "id", "", rows)

      # Images (glance)
      cur.execute("select * from glance.images where owner = %s and status != 'deleted' and is_public = 0", (tenant_id))
      rows = cur.fetchall()
      if args.delete:
        delete_images(rows)
      else:
        print_output("Images", "id", "name", rows)

con.close()
