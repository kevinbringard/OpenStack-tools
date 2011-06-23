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

set -e

glance_upload=$( which glance-upload )
##
# Use this to force a glance-upload location if it's not in your path (or to override the above if you're so inclined)
# Normally this should be commented out and should only be used if you're really sure you know what you're doing
# glance_upload="/usr/bin/glance-upload"

glance=$( which glance )
##
# Use this to force a glance location (just like the above for glance-upload), same caveats apply
# glance="/usr/bin/glance"

username=$( whoami )
host=$( hostname )

args=$( getopt :i:k:r:v:d:e:a:h:p: $*)

usage() {
  echo "USAGE: $0 [options]
  -i  Path to the image to upload
  -k  Path to the kernel to upload
  -r  Path to the ramdisk to upload

Host is required if you are connecting to a remote glance server, port will default to 9292
  -h  Host to connect to
  -p  Port to connect to

The options below here are required for meta-data, so be descriptive
  -v  The version of the OS you are uploading
  -d  The distro you are uploading (CentOS, RHEL, Ubuntu, etc)
  -e  The kernel version (2.6.28, 2.6.32-el6, or whatever), required if you are uploading a kernel
  -a  The architecture of the image (x86_64, amd64, i386, etc)
  "
  exit 1
}

check_for_dupes() {
  breakout=1
  if [ -z $name_version ]; then
    name_version=1
  else
    name_version=$( echo "$name_version + 1" | bc )
  fi

  for i in $( $glance index | grep -v "public images" | grep -v "Disk Format" | grep -v "\-\-\-\-\-\-\-\-\-\-\-" | awk '{ print $2 }' ); do
    if [ -z $i ]; then
      return
    fi

    if [ ! -z $ramdisk_name ] && [ $ramdisk_name == $i ]; then
      ramdisk_name=$( echo "$ramdisk-$name_version" )
      breakout=0
    elif [ ! -z $kernel_name ] && [ $kernel_name == $i ]; then
      kernel_name=$( echo "$kernel-$name_version" )
      breakout=0
    elif [ $image_name == $i ]; then
      image_name=$( echo "$image-$name_version" )
      breakout=0
    fi
  done
  if [ $breakout -eq 0 ]; then
    check_for_dupes
  fi
}

if [ -z $1 ]; then
  usage
fi

eval set -- $args

for i; do
  case "$i" in
    -i) shift; image=$1; shift;;
    -k) shift; kernel=$1; shift;;
    -r) shift; ramdisk=$1; shift;;
    -v) shift; version=$1; shift;;
    -d) shift; distro=$1; shift;;
    -e) shift; kernel_version=$1; shift;;
    -a) shift; arch=$1; shift;;
    -h) shift; host=$1; shift;;
    -p) shift; port=$1; shift;;
  esac
done

if [ ! -z $host ]; then
  glance_upload=$( echo "$glance_upload --host $host" )
  glance=$( echo "$glance -H $host" )
fi

if [ ! -z $port ]; then
  glance_upload=$( echo "$glance_upload --port $port" )
  glance=$( echo "$glance -p $port" )
fi

if [ -z $distro ] || [ -z $version ]; then
  echo "You must provide the OS version and Distro with -d and -v!"
  usage
fi

ramdisk_name=$ramdisk
kernel_name=$kernel
image_name=$image

check_for_dupes

if [ ! -z $ramdisk ]; then
  $glance_upload --disk-format=ari --container-format=ari --type=ramdisk $ramdisk $ramdisk_name
  ramdisk_id=$( $glance index | awk '{ print $1, $2 }' | egrep "(${ramdisk_name}$)" | awk '{ print $1}' )
fi

if [ ! -z $kernel ]; then
  if [ -z $kernel_version ]; then
    echo "If you provide a kernel, you must also provide a version with -e!"
    usage
  fi
  $glance_upload --disk-format=aki --container-format=aki --type=kernel $kernel $kernel_name
  kernel_id=$( $glance index | awk '{ print $1, $2 }' | egrep "(${kernel_name}$)" | awk '{ print $1 '} )
fi

if [ -z $image ]; then
  usage
elif [ -z $kernel_id ] && [ -z $ramdisk_id ]; then
  $glance_upload --disk-format=ami --container-format=ami --type=machine $image $image_name
elif [ -z $kernel_id ] && [ ! -z $ramdisk_id ]; then
  $glance_upload --disk-format=ami --container-format=ami --type=machine --ramdisk=$ramdisk_id $image $image_name
elif [ ! -z $kernel_id ] && [ -z $ramdisk_id ]; then
  $glance_upload --disk-format=ami --container-format=ami --type=machine --kernel=$kernel_id $image $image_name
elif [ ! -z $kernel_id ] && [ ! -z $ramdisk_id ]; then
  $glance_upload --disk-format=ami --container-format=ami --type=machine --kernel=$kernel_id --ramdisk=$ramdisk_id $image $image_name
else
  echo "Something seems to have gone wrong... I'm outa here"
  exit 1
fi

image_id=$( $glance index | awk '{ print $1, $2 }' | egrep "(${image_name}$)" | awk '{ print $1 '} )
echo "Setting the required properties..."
$glance update $image_id type=machine version="$version" distro="$distro" uploader="$username@$host" arch="$arch"
if [ ! -z $kernel_id ] && [ ! -z $kernel_version ]; then
  $glance update $image_id type=machine version="$version" distro="$distro" uploader="$username@$host" arch="$arch" kernel_id="$kernel_id" kernel_name="$kernel_name"
  $glance update $kernel_id type=kernel version="$kernel_version" distro="$distro" uploader="$username@$host" arch="$arch"
fi 

if [ ! -z $ramdisk_id ] && [ ! -z $kernel_id ]; then
  $glance update $image_id type=machine version="$version" distro="$distro" uploader="$username@$host" arch="$arch" kernel_id="$kernel_id" kernel_name="$kernel_name" ramdisk_id="$ramdisk_id" ramdisk_name="$ramdisk_name"
  $glance update $ramdisk_id type=ramdisk distro="$distro" uploader="$username@$host" arch="$arch"
fi

if [ ! -z $ramdisk_id ] && [ -z $kernel_id ]; then
  $glance update $image_id type=machine version="$version" distro="$distro" uploader="$username@$host" arch="$arch" ramdisk_id="$ramdisk_id" ramdisk_name="$ramdisk_name"
  $glance update $ramdisk_id type=ramdisk distro="$distro" uploader="$username@$host" arch="$arch"
fi
