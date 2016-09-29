#!/usr/bin/env bash

cd git && git clone https://git.openstack.org/openstack-dev/devstack && cd devstack && git checkout stable/mitaka
cp /vagrant/local.conf .
./stack.sh

source ${HOME}/git/devstack/openrc admin admin
nova flavor-create m1.tiny.hugepage auto 512 0 1
nova flavor-key m1.tiny.hugepage set hw:mem_page_size=2048
