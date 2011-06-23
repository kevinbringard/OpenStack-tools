#!/usr/bin/env bash

##
# Copyright (c) 2011 Kevin Bringard
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
##

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
