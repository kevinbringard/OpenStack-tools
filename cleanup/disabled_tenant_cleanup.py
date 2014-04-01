#!/usr/bin/env python

import MySQLdb as mdb
import sys
import os
import argparse
import simplejson as json
from novaclient.v1_1 import client as nova
from cinderclient import client as cinder
from neutronclient.neutron import client as neutron

def parse_args():
  # ensure environment has necessary items to authenticate
  for key in ['OS_TENANT_NAME', 'OS_USERNAME', 'OS_PASSWORD',
      'OS_AUTH_URL']:
    if key not in os.environ.keys():
      print "Your environment is missing, please source your OpenStack credentials"
      exit(1)

  ap = argparse.ArgumentParser(description=DESCRIPTION)
  ap.add_argument('-d', '--delete', action='store_true',
      default=False, help='Delete active resources')

  return ap.parse_args()

def delete_instances(instance_uuids):
  nova_client = nova.Client(username, password, project_id, auth_url)

  for row in instance_uuids:
    instance_uuid = row['uuid']
    if not instance_uuid:
      print "I couldn't find any instances"
    else:
      print "Deleting instance: %s" % instance_uuid
      os.system("nova delete %s" % instance_uuid)

def delete_snapshots(snapshot_uuids):

  for row in snapshot_uuids:
    snapshot_uuid = row["id"]
    print "Deleting snapshot %s" % snapshot_uuid
    os.system("cinder snapshot-delete %s" % snapshot_uuid)

def delete_volumes(volume_uuids):

  for row in volume_uuids:
    volume_uuid = row['id']
    print "Deleting volume %s" % volume_uuid
    os.system("cinder delete %s" % volume_uuid)

def delete_images(image_uuids):

  for row in image_uuids:
    image_uuid = row['id']
    print "Deleting image %s" % image_uuid
    os.system("glance image-delete %s" % image_uuid)

def network_cleanup(tenant_id):

  # First we have to cleanup any leftover floating IPs
  # neutron floatingip-delete <floatingip-id>
  cur.execute("select * from neutron.floatingips where tenant_id = %s ;", (tenant_id))
  floating_rows = cur.fetchall()
  for row in floating_rows:
    floating_uuid = row['id']
    floating_ip = row['floating_ip_address']
    fixed_ip = row['fixed_ip_address']
    if not fixed_ip and floating_ip:
      print "IP %s has no fixed_ip. Deleting." % floating_ip
      os.system("neutron floatingip-delete %s" % floating_uuid)
    if fixed_ip and floating_ip:
      print "IP %s still has fixed_ip %s" % floating_ip, fixed_ip

  # Then we need to clear the router's gateway
  # neutron router-gateway-clear router1
  cur.execute("select * from neutron.routers where tenant_id = %s ;", (tenant_id))
  router_rows = cur.fetchall()
  for row in router_rows:
    router_uuid = row['id']
    gateway_port_id = row['gw_port_id']
    if not gateway_port_id:
      print "It looks like router %s doesn't have a gateway, skipping" % router_uuid
    else:
      os.system("neutron router-gateway-clear %s" % router_uuid)

    # Then we remove the subnet(s) from the router
    # neutron router-interface-delete router1 <subnet-id>
    # cur.execute("select * from neutron.subnets where tenant_id = %s ;", (tenant_id))
    cur.execute("select * from neutron.subnets where network_id = (select network_id from neutron.ports where device_id = '%s' and device_owner = 'network:router_interface');" % router_uuid)
    subnet_rows = cur.fetchall()
    for row in subnet_rows:
      subnet_uuid = row['id']
    if not subnet_uuid:
      print "I couldn't find any subnets to remove"
    else:
      os.system("neutron router-interface-delete %s %s" % (router_uuid, subnet_uuid))
      os.system("neutron subnet-delete %s" % subnet_uuid)

  # Finally, delete the router itself
  # neutron router-delete router1
  cur.execute("select * from neutron.routers where tenant_id = %s ;", (tenant_id))
  router_rows = cur.fetchall()
  for row in router_rows:
    router_uuid = row['id']
    router_name = row['name']
    if not router_uuid:
      print "I couldn't find any more routers"
    else:
      os.system("neutron router-delete %s" % router_uuid)

  # Now we delete the networks
  cur.execute("select * from neutron.networks where tenant_id = %s ;", (tenant_id))
  network_rows = cur.fetchall()
  for row in network_rows:
    network_uuid = row['id']
    network_name = row['name']
    if not network_uuid:
      print "I couldn't find any more networks"
    else:
      os.system("neutron net-delete %s" % network_uuid)

  # And the load balancers (pools)
  cur.execute("select * from neutron.pools where tenant_id = %s ;", (tenant_id))
  lb_rows = cur.fetchall()
  for row in lb_rows:
    lb_uuid = row['id']
    os.system("neutron lb-pool-delete %s" % lb_uuid)

  # And the VIPs
  cur.execute("select * from neutron.vips where tenant_id = %s ;", (tenant_id))
  vip_rows = cur.fetchall()
  for row in vip_rows:
    vip_uuid = row['id']
    os.system("neutron lb-vip-delete %s" % vip_uuid)

  # Then do one more pass for any leftover ports
  cur.execute("select * from neutron.ports where tenant_id = %s ;", (tenant_id))
  port_rows = cur.fetchall()
  for row in port_rows:
    port_uuid = row['id']
    os.system("neutron port-delete %s" % port_uuid)

def print_output(field_type, uuid_field, name_field, rows):
  print "  %s:" % field_type
  for row in rows:
    uuid = row[uuid_field]
    if not name_field:
      name = ""
    else:
      name = row[name_field]
    print "    %s (%s)" % (uuid, name)

# Parse our arguments
DESCRIPTION = "OpenStack Resource Cleanup Tool"
args = parse_args()

# Setup our environment
username=os.environ['OS_USERNAME']
password=os.environ['OS_PASSWORD']
auth_url=os.environ['OS_AUTH_URL']
project_id=os.environ['OS_TENANT_NAME']
tenant_id=os.environ['OS_TENANT_NAME']

# Put your DB creds here
# Your DB creds need SELECT on neutron.*
# nova.*, cinder.* and glance.*
DB_USER="USER"
DB_PASS="PASS"
DB_HOST="HOST"

# Do the thing
con = mdb.connect(DB_HOST, DB_USER, DB_PASS)
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
    if args.delete:
      delete_instances(rows)
    else:
      print_output("Instances", "uuid", "hostname", rows)

    # Cleanup the network
    if args.delete:
      network_cleanup(tenant_id)

    # Snapshots
    cur.execute("select * from cinder.snapshots where project_id = %s and deleted = 0;", (tenant_id))
    rows = cur.fetchall()
    if args.delete:
      delete_snapshots(rows)

    # Volumes
    cur.execute("select * from cinder.volumes where project_id = %s and deleted = 0 ;", (tenant_id))
    rows = cur.fetchall()
    if args.delete:
      delete_volumes(rows)

    # Images (glance)
    cur.execute("select * from glance.images where owner = %s and status != 'deleted' and is_public = 0", (tenant_id))
    rows = cur.fetchall()
    if args.delete:
      delete_images(rows)

con.close()
