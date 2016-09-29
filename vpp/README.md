## Synopsis

Standup a vagrant box suitable for running devstack with the VPP plugin on CentOS7. Incudes the vagrant file, and scripts
to perform the basic install/config

## Getting started

### Stand up the Vagrant box and login
vagrant up && vagrant ssh

### Copy the vagrant files to /home/vagrant
cp /vagrant .

### Make sure you're running the latest kernel and libs
sudo yum -y update

### Setup hugepages and NUMA isolation
sudo sed -i 's/rhgb quiet/rhgb quiet default_hugepagesz=2M hugepagesz=2M hugepages=2048 iommu=pt intel_iommu=on isolcpus=0-3/' /etc/default/grub
sudo grub2-mkconfig -o /boot/grub2/grub.cfg

### Reboot
sudo reboot

### Run the setup_vpp.bash script. It will take some time
./setup_vpp.bash

### Verify vpp is up and running properly (the setup_vpp script also dumps this info)
sudo vppctl show int

### Run setup_devstack.bash
./setup_devstack.bash

## That's it!
When this finishes you should have a running devstack with the VPP plugin. It's worth noting at this time we're still working though some issues with Virtualbox and NUMA so it's likely you'll run into issues actually launching VMs, but neautron port-create commands *should* work
