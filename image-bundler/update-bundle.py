#!/usr/bin/env python

import os
# pip install requests
import requests
import subprocess
import sys
import tarfile
import tempfile
import urllib2
# pip install pyyaml
import yaml

from datetime import datetime

config_file = "archive_config.yml"
image_files = []
TODAY = datetime.today().strftime('%Y-%m-%d')
build_bundle = False

with open(config_file, 'r') as stream:
    try:
        config = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)


def check_for_update(local_absolute_file, url, local_modified):
    request = urllib2.Request(url)
    opener = urllib2.build_opener()
    data = opener.open(request)
    remote_modified = data.headers.dict['last-modified']
    remote_modified = datetime.strptime(remote_modified,
                                        '%a, %d %b %Y %H:%M:%S %Z')
    print "Remote modified: %s" % remote_modified
    print "Local modified: %s" % local_modified
    if remote_modified > local_modified:
        print "Remote file is newer"
        return True
    elif remote_modified < local_modified:
        print "Local file is newer, skipping"
        return False
    elif remote_modified == local_modified:
        print "The files appear to have the same timestamp"
        return False


def download_image(url, local_file):
    print "Downloading image to %s from %s" % (local_file, url)
    with open(local_file, 'wb') as f:
        response = requests.get(url, stream=True)
        total_length = response.headers.get('content-length')

        if total_length is None:
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=4096):
                dl += len(data)
                f.write(data)
                done = int(50 * dl / total_length)
                sys.stdout.write("\rProgress: [%s>%s]" %
                                 ('=' * done, ' ' * (50-done)))
                sys.stdout.flush()
    return True


def convert_to_raw(tmpfile, outputfile):
    print "converting %s to raw" % tmpfile
    subprocess.call(['qemu-img', 'convert', '-O', 'raw', tmpfile, outputfile])
    print "Converted %s to raw and saved as %s" % (tmpfile, outputfile)


def get_image_format(local_absolute_file):
    cmd = ['qemu-img', 'info', local_absolute_file]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    for line in proc.stdout.readlines():
        if line.find('file format: qcow2') == 0:
            return "qcow2"
        if line.find('file format: raw') == 0:
            return "raw"
    return "something else"


def create_bundle(bundle_name, image_files, compress):
    if compress:
        tar = tarfile.open(bundle_name, 'w:gz')
    else:
        tar = tarfile.open(bundle_name, 'w')

    for filename in image_files:
        if os.path.isfile(filename):
            tar.add(filename)
    tar.close()

for key, value in config['images'].iteritems():
    filename = "%s-%s.%s" % (value['localname'], TODAY, value['extension'])
    local_absolute_file = os.path.join(value['path'], filename)
    print ""
    print "Processing %s..." % key
    if os.path.isfile(local_absolute_file):
        local_modified = datetime.utcfromtimestamp(
            os.path.getmtime(local_absolute_file))
        updated = check_for_update(local_absolute_file, value['url'],
                                   local_modified)
        if not updated:
            image_files.append(local_absolute_file)
    if not os.path.isfile(local_absolute_file) or updated:
        tmp = tempfile.NamedTemporaryFile(delete=True)
        image_downloaded = download_image(value['url'], tmp.name)
        if image_downloaded:
            build_bundle = True
            filetype = get_image_format(tmp.name)
            if filetype != "raw":
                convert_to_raw(tmp.name, local_absolute_file)
                image_files.append(local_absolute_file)
            else:
                image_files.append(local_absolute_file)

        tmp.close()

if build_bundle:
    for key, value in config['archives'].iteritems():
        print "Processing archive %s" % key
        bundle_name_and_path = os.path.join(value['path'], value['name'])
        create_bundle(bundle_name_and_path, image_files, value['compress'])
