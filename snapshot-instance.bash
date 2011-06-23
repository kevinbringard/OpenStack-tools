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

## 
# This script will allow you to snapshot a running instance to upload into glance as a new iterative instance

usage() {
  echo "USAGE: $0 [options]
  -i  Instance to snap
  -n  Name of the new instance (defaults to instance-id-date +\'%Y-%h-%d-%H%M%S\')
  -d  Directory to save the new instance to (defaults to /tmp)
  -p  Path to instances (defaults to /var/lib/nova/instances/)"

  exit 1
}

args=$( getopt :i:n:d:p: $* )

eval set -- $args

for i; do
  case "$i" in
    -i) shift; instance=$1; shift;;
    -n) shift; name=$1; shift;;
    -d) shift; directory=$1; shift;;
    -p) shift; path=$1; shift;;
  esac
done

if [ -z $instance ]; then
  echo "You must specify an instance ID!"
  usage
fi

instance=$( echo "$instance" | sed 's/i-/instance-/' )

if [ ! -z $directory ] && [ ! -d $directory ]; then
  echo "$directory doesn't seem to exist, creating it..."
  mkdir -p $directory
fi

# Set our defaults here
if [ -z $name ]; then
  name=$( echo "$instance-$( date +'%Y-%h-%d-%H%M%S' )" )
fi

if [ -z $directory ]; then
  directory="/tmp"
fi

if [ -z $path ]; then
  path="/var/lib/nova/instances"
fi

qemu_img=$( which qemu-img )
if [ -z $qemu_img ]; then
  echo "I couldn't find qemu-img, are you sure it's installed?"
  usage
fi

# If the instance doesn't exist then we can't very well snapshot it
if [ ! -f $path/$instance/disk ]; then
  echo "I couldn't find $path/$instance"
  usage
fi
diskfile="$path/$instance/disk"
snapname="snap-$( date +'%Y-%h-%d-%H%M%S' )"

$qemu_img snapshot -c $snapname $diskfile
cd $path/$instance && $qemu_img convert -O qcow2 -s $snapname disk $directory/$name

echo "Your new image should now be in $directory/$name"
echo "Don't forget that if it was associated with a kernel, you will need to associate this with the same kernel when you upload it into your image store"
