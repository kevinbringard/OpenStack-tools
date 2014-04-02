#!/usr/bin/env python

import MySQLdb as mdb
import sys
import os
import subprocess
import argparse

# Your DB creds need SELECT on neutron.*
# nova.*, cinder.* and glance.*
DB_USER=""
DB_PASS=""
DB_HOST=""

# For argparse
DESCRIPTION = "OpenStack Resource Cleanup Tool"

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

  for row in instance_uuids:
    instance_uuid = row['uuid']
    if not instance_uuid:
      print "I couldn't find any instances"
    else:
      print "Deleting instance: %s" % instance_uuid
      subprocess.check_call(["nova", "delete", instance_uuid])

def delete_snapshots(snapshot_uuids):

  for row in snapshot_uuids:
    snapshot_uuid = row["id"]
    print "Deleting snapshot %s" % snapshot_uuid
    subprocess.check_call(["cinder", "snapshot-delete", snapshot_uuid])

def delete_volumes(volume_uuids):

  for row in volume_uuids:
    volume_uuid = row['id']
    print "Deleting volume %s" % volume_uuid
    subprocess.check_call(["cinder", "delete", volume_uuid])

def delete_images(image_uuids):

  for row in image_uuids:
    image_uuid = row['id']
    print "Deleting image %s" % image_uuid
    subprocess.check_call(["glance", "image-delete", image_uuid])

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
      subprocess.check_call("[neutron", "floatingip-delete", floating_uuid])
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
      subprocess.check_call(["neutron", "router-gateway-clear", router_uuid])

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
      subprocess.check_call(["neutron", "router-interface-delete", router_uuid, subnet_uuid])
      subprocess.check_call(["neutron", "subnet-delete", subnet_uuid])

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
      subprocess.check_call(["neutron", "router-delete", router_uuid])

  # Now we delete the networks
  cur.execute("select * from neutron.networks where tenant_id = %s ;", (tenant_id))
  network_rows = cur.fetchall()
  for row in network_rows:
    network_uuid = row['id']
    network_name = row['name']
    if not network_uuid:
      print "I couldn't find any more networks"
    else:
      subprocess.check_call(["neutron", "net-delete", network_uuid])

  # And the load balancers (pools)
  cur.execute("select * from neutron.pools where tenant_id = %s ;", (tenant_id))
  lb_rows = cur.fetchall()
  for row in lb_rows:
    lb_uuid = row['id']
    subprocess.check_call(["neutron", "lb-pool-delete", lb_uuid])

  # And the VIPs
  cur.execute("select * from neutron.vips where tenant_id = %s ;", (tenant_id))
  vip_rows = cur.fetchall()
  for row in vip_rows:
    vip_uuid = row['id']
    subprocess.check_call(["neutron", "lb-vip-delete", vip_uuid])

  # Then do one more pass for any leftover ports
  cur.execute("select * from neutron.ports where tenant_id = %s ;", (tenant_id))
  port_rows = cur.fetchall()
  for row in port_rows:
    port_uuid = row['id']
    subprocess.check_call(["neutron", "port-delete", port_uuid])

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
args = parse_args()

# Setup our openstack environment
username=os.environ['OS_USERNAME']
password=os.environ['OS_PASSWORD']
auth_url=os.environ['OS_AUTH_URL']
project_id=os.environ['OS_TENANT_NAME']
tenant_id=os.environ['OS_TENANT_NAME']

# Make sure we set the DB env
if not DB_HOST or not DB_USER or not DB_PASS:
  print "You must specify DB_HOST, DB_USER and DB_PASS"
  exit(1)

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
