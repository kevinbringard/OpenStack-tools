#!/usr/bin/env bash

INTERFACES="eth1 eth2"
PACKAGES="git pciutils lshw python-devel etcd"

# Set the branch we want to checkout
VPP_SHA="stable/1609"

# Define our git directory
GIT_DIR="${HOME}/git"
VPP_DIR="${GIT_DIR}/vpp"

# Turn down eth1 and eth2
for i in $INTERFACES; do
  sudo ip link set $i down
done

# Install $PACKAGES
for i in $PACKAGES; do
  sudo yum install -y $i
done

# Checkout VPP
mkdir -p ${GIT_DIR}
cd ${GIT_DIR}

if [ ! -d ${GIT_DIR}/vpp ]; then
  git clone https://gerrit.fd.io/r/vpp && cd ${VPP_DIR}
  echo "VPP Checked out in ${VPP_DIR}"
else
  echo "VPP already looks to be checked out in ${VPP_DIR}"
fi

if [ VPP_SHA != "" ]; then
  git checkout $VPP_SHA
  echo "Checked out commit $VPP_SHA"
fi

# Fix the makefile to not promp
# sed -i.bak 's/$(CONFIRM)/-y/g' Makefile

# Build VPP
cd ${VPP_DIR}
make install-dep && make build-release && make pkg-rpm

# Install the built RPMs
sudo yum install -y ${VPP_DIR}/build-root/vpp*.rpm

# Build the python-api
make -Cbuild-root PLATFORM=vpp TAG=vpp_debug vpp-api-install
cd ${VPP_DIR}/vpp-api/python
sudo python setup.py install

# Insert the igb_uio.ko module
sudo ln -s ${VPP_DIR}/build-root/install-vpp-native/dpdk/kmod/igb_uio.ko /lib/modules/$( uname -r )
sudo depmod -a
sudo modprobe igb_uio

# Create the vpp startup.conf, backing up the existng one if it exists
if [ -f /etc/vpp/startup.conf.orig ]; then
  echo "Skipping backup"
  sudo mv /vagrant/startup.conf /etc/vpp/startup.conf
else
  sudo mv /etc/vpp/startup.conf /etc/vpp/startup.conf.orig
  sudo mv /vagrant/startup.conf /etc/vpp/startup.conf
fi

sudo sysctl -w vm.nr_hugepages=1024
sudo sysctl -w vm.max_map_count=3096
sudo sysctl -w vm.hugetlb_shm_group=0

sudo sed -i.bak 's/2379/4001/g' /etc/etcd/etcd.conf
sudo systemctl restart etcd

# Startup VPP
sudo systemctl start vpp

# Show interfaces
sudo vppctl show interface
