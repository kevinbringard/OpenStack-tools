## Synopsis

Standup a vagrant box suitable for running devstack with the VPP plugin on CentOS7. Incudes the vagrant file, and scripts
to perform the basic install/config

## Getting started

### Stand up the Vagrant box and login
vagrant up --provider=vmware_fusion
vagrant ssh

### Run the install_vpp_rpms.bash script. This installs VPP and its python API from the VPP repos
cd /vagrant
./install_vpp_rpms.bash

### Verify vpp is up and running properly (the install_vpp_rpms.bash script also dumps this info)
sudo vppctl show int

### Run setup_devstack.bash
./setup_devstack.bash

### Restart q-svc (neutron-server) by the normal devstack means. This is due to a bug in the ML2 driver, it may be unecessary later.

### Restart n-sch (nova scheduler) by the normal devstack means. This is to make sure the NUMATopologyFilter scheduling filter takes effect.

### Restart n-cpu (nova-compute) by the normal devstack means. This is to ensure it's using the correct qemu binary and populating the nova.compute_nodes.numa_topology correctly

### Create a new neutron-network and subnet. This appears to be necessary due to a bug in the ML2 driver which doesn't corretly plumb in DHCP services for existing networks
neutron net-create my-vpp-net
neutron subnet-create my-vpp-net 10.254.254.0/24 --name my-vpp-subnet

### Spin up a VM on the new network
nova boot --image cirros-0.3.4-x86_64-uec --flavor m1.tiny.hugepage --nic net-name=my-vpp-net vpp-test-1

## That's it!
