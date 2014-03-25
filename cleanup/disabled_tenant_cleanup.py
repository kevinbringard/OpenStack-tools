#!/usr/bin/env python

import MySQLdb as mdb
import sys
import os
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

def delete_instances(instance_uuids):
  nova_client = nova.Client(username, password, project_id, auth_url)

  # for instance_uuid in instance_uuids:
  # nova_client.servers.delete(instance_uuid)

def delete_snapshots(snapshot_uuids):
  cinder_client = cinder.Client('1', username, password, project_id, auth_url)

  # for snapshot_uuid in snapshot_uuids:
  # cinder_client.snapshot.delete(snapshot_uuid)

def delete_volumes(volume_uuids):
  cinder_client = cinder.Client('1', username, password, project_id, auth_url)

  # for volume_uuid in volume_uuids:
  # cinder_client.volumes.delete()

def delete_ports(port_uuids):
  """
  # neutron_client = neutron.Client('2.0', auth_url, tenant_id, username, password)

  #for port_uuid in port_uuids:
  # neutron_client.delete_port(port_uuid)

  # print neutron_client.list_networks()
  """

# You'll need to put your DB creds in here. You'll need
# SELECT on nova.*, cinder.*, neutron.* and glance.*
con = mdb.connect('HOST', 'USER', 'PASS')

with con:
  cur = con.cursor(mdb.cursors.DictCursor)

  cur.execute("select * from keystone.project where enabled = 0")

  rows = cur.fetchall()

  if rows:
    for row in rows:
      tenant_id = row["id"]
      name = row["name"]
      print "Tenant: %s (%s)" % (tenant_id, name)

      # Instances
      cur.execute("select * from nova.instances where project_id = %s and deleted = 0 ;", (tenant_id))
      rows = cur.fetchall()
      print "  Instances:"
      for row in rows:
        uuid = row["uuid"]
        name = row["hostname"]
        print "    %s (%s)" % (uuid, name)

      # Routers
      cur.execute("select * from neutron.routers where tenant_id = %s ;", (tenant_id))
      rows = cur.fetchall()
      print "  Routers:"
      for row in rows:
        uuid = row["id"]
        name = row["name"]
        print "    %s (%s)" % (uuid, name)

      # Networks
      cur.execute("select * from neutron.networks where tenant_id = %s ;", (tenant_id))
      rows = cur.fetchall()
      print "  Networks:"
      for row in rows:
        uuid = row["id"]
        name = row["name"]
        print "    %s (%s)" % (uuid, name)

      # Subnets
      cur.execute("select * from neutron.subnets where tenant_id = %s ;", (tenant_id))
      rows = cur.fetchall()
      print "  Subnets:"
      for row in rows:
        uuid = row["id"]
        name = row["name"]
        print "    %s (%s)" % (uuid, name)

      # Floating IPs
      cur.execute("select * from neutron.floatingips where tenant_id = %s ;", (tenant_id))
      rows = cur.fetchall()
      print "  Floating IPs:"
      for row in rows:
        uuid = row["id"]
        name = row["floating_ip_address"]
        print "    %s (%s)" % (uuid, name)

      # Load balancers
      cur.execute("select * from neutron.pools where tenant_id = %s ;", (tenant_id))
      rows = cur.fetchall()
      print "  LB Pools:"
      for row in rows:
        uuid = row["id"]
        name = row["name"]
        print "    %s (%s)" % (uuid, name)

      cur.execute("select * from neutron.vips where tenant_id = %s ;", (tenant_id))
      rows = cur.fetchall()
      print "  LB VIPs:"
      for row in rows:
        uuid = row["id"]
        name = row["name"]
        print "    %s (%s)" % (uuid, name)

      # Ports
      cur.execute("select * from neutron.ports where tenant_id = %s ;", (tenant_id))
      rows = cur.fetchall()
      print "  Ports:"
      for row in rows:
        uuid = row["id"]
        name = row["name"]
        print "    %s (%s)" % (uuid, name)

      # Snapshots
      cur.execute("select * from cinder.snapshots where project_id = %s and deleted = 0;", (tenant_id))
      rows = cur.fetchall()
      print "  Snapshots:"
      for row in rows:
        uuid = row["id"]
        print "    %s" % (uuid)

      # Volumes
      cur.execute("select * from cinder.volumes where project_id = %s and deleted = 0 ;", (tenant_id))
      rows = cur.fetchall()
      print "  Volumes:"
      for row in rows:
        uuid = row["id"]
        print "    %s" % (uuid)

      # Images
      cur.execute("select * from glance.images where owner = %s and status != 'deleted' and is_public = 0", (tenant_id))
      rows = cur.fetchall()
      print "  Images:"
      for row in rows:
        uuid = row["id"]
        name = row["name"]
        print "    %s (%s)" % (uuid, name)

con.close()
