#!/usr/bin/env bash

echo "Installing the EPEL repo..."
rpm -Uvh 'http://download.fedora.redhat.com/pub/epel/5/x86_64/epel-release-5-4.noarch.rpm'

echo "Installing dependencies from the epel repo..."
yum -y install python-cheetah python-configobj python26 sudo python26-distribute

echo "Installing cheetah and configobj"
easy_install-2.6 cheetah
easy_install-2.6 configobj
easy_install-2.6 pyyaml

echo "Installing cloud-init..."
rpm -ivh python-yaml-3.09-1.el5.rf.noarch.rpm
rpm -ivh cloud-init-0.5.14-23.amzn1.noarch.rpm

mv configs/* /etc/cloud/
