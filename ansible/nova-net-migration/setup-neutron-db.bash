#!/usr/bin/env bash

# Full path to your RC file.
# It should have the SQL passwords in it as well (see below)
RC_FILE="/tmp/openrc.sh"

source /tmp/openrc.sh

mysqladmin -u root -p$MYSQL_ROOT_PASSWORD -f drop neutron_ml2 || true
mysql -u root -p$MYSQL_ROOT_PASSWORD -e 'CREATE DATABASE neutron_ml2 CHARACTER SET utf8;'

neutron-db-manage --config-file /etc/neutron/neutron.conf --config-file /etc/neutron/plugins/ml2/ml2_conf.ini upgrade head
