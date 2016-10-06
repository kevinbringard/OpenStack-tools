sudo ip link set eth0 down
sudo ip link set eth1 down
sudo cp /vagrant/fdio-release.repo /etc/yum.repos.d/
sudo yum -y install vpp vpp-devel vpp-plugins
sudo yum -y install https://github.com/vpp-dev/vpp/raw/1609-python/RPMs/vpp-python-api-16.09-release.x86_64.rpm
sudo mv /etc/vpp/startup.conf /etc/vpp/startup.conf.bak
sudo cp /vagrant/startup.conf /etc/vpp/startup.conf
sudo sysctl -w vm.nr_hugepages=2048
sudo sysctl -w vm.max_map_count=3096
sudo sysctl -w vm.hugetlb_shm_group=0
sudo systemctl start vpp
sudo vppctl show int
