#!/usr/bin/env bash

PACKAGES="git pciutils lshw python-devel etcd gcc"

# Install $PACKAGES
for i in $PACKAGES; do
  sudo yum install -y $i
done

sudo sed -i.bak 's/2379/4001/g' /etc/etcd/etcd.conf
sudo systemctl restart etcd

GIT_DIR=${HOME}/git
DEVSTACK_DIR=${GIT_DIR}/devstack

mkdir -p ${GIT_DIR}

cd ${GIT_DIR} && git clone https://git.openstack.org/openstack-dev/devstack && cd ${DEVSTACK_DIR} && git checkout stable/mitaka
cp /vagrant/local.conf ${DEVSTACK_DIR}
${DEVSTACK_DIR}/stack.sh

source ${DEVSTACK_DIR}/openrc admin admin
nova flavor-create m1.tiny.hugepage auto 512 0 1
nova flavor-key m1.tiny.hugepage set hw:mem_page_size=2048
sudo yum -y remove qemu-system-x86
sed -i 's/SameHostFilter,DifferentHostFilter/SameHostFilter,DifferentHostFilter,NUMATopologyFilter'/ /etc/nova/nova.conf
