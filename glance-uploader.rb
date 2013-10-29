#!/usr/bin/env ruby

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
###

# gem install ogle
require 'ogle'
require 'optparse'

# Define our options
options = {}

optparse = OptionParser.new do |opts|
  opts.banner = "Usage: #{$0} -i|--image file -v|--version version -d|--distro distribution -a|--arch architecture [-u|--user user] [ -P|--pass password] [-H|--host host] [-p|--port port] [-n|--name name] [-r|-ramdisk ramdisk] [-k|--kernel kernel] [-e|--kernel_version kernel_version] [-s|--storage ENGINE] [-c|--custom_fields field1=1,field2=2]"

  options[:host] = "localhost"
  opts.on( '-H', '--host HOST', 'Glance host to connect to (defaults to localhost)') do |host|
    options[:host] = host
  end

  options[:port] = "9292"
  opts.on( '-p', '--port PORT', 'Glance port to connect to (defaults to 9292)') do |port|
    options[:port] = port
  end

  options[:user] = nil
  opts.on( '-u', '--user USER', 'Username to authenticate with') do |user|
    options[:user] = user
  end

  options[:pass] = nil
  opts.on( '-P', '--pass PASSWORD', 'Password to authenticate with') do |pass|
    options[:pass] = pass
  end

  options[:image] = nil
  opts.on( '-i', '--image FILE', 'Machine image to upload (required)') do |image|
    options[:image] = image
  end

  options[:name] = nil
  opts.on( '-n', '--name NAME', 'Name to give the image when it has been uploaded (defaults to distro_version-arch)') do |name|
    options[:name] = name
  end

  options[:ramdisk] = nil
  opts.on( '-r', '--ramdisk [FILE|ID]', 'Ramdisk image to upload, or existing ID to link to') do |ramdisk|
    options[:ramdisk] = ramdisk
  end

  options[:kernel] = nil
  opts.on( '-k', '--kernel [FILE|ID]', 'Kernel image to upload, or existing ID to link to') do |kernel|
    options[:kernel] = kernel
  end

  options[:version] = nil
  opts.on( '-v', '--version VERSION', 'The version of the OS you are uploading (required)') do |version|
    options[:version] = version
  end

  options[:distro] = nil
  opts.on( '-d', '--distro DISTRO', 'The distribution you are uploading (Ubuntu, CentOS, Debian, etc) (required)') do |distro|
    options[:distro] = distro
  end

  options[:storage] = nil
  opts.on( '-s', '--storage ENGINE', [:file, :s3, :swift ], 'The storage engine to use, valid options are file, s3, or swift. If you don\'t specify one it uses the glance default (currently file)') do |storage|
    options[:storage] = storage
  end

  options[:kernel_version] = nil
  opts.on( '-e', '--kernel_version VERSION', 'The kernel version (2.6.28, 2.6.32-el6, etc). Required if you are uploading a kernel') do |kernel_version|
    options[:kernel_version] = kernel_version
  end

  options[:arch] = nil
  opts.on( '-a', '--arch ARCH', 'The architecture of the image (x86_64, amd64, i386, etc) (required)') do |arch|
    options[:arch] = arch
  end

  options[:custom] = []
  opts.on( '-c', '--custom_fields a=1,b=2,c=3', Array, 'Custom fields you wish to define') do |custom|
    options[:custom] = custom
  end

  opts.on( '-h', '--help', 'Display the help screen' ) do
    puts opts
    exit
  end

  if ARGV.empty?
    puts opts
    exit
  end

end

optparse.parse!

# These options are required
unless options[:distro] && options[:version] && options[:arch]
  puts "You seem to be missing a required option"
  puts optparse
  exit
end

# Set the name to be "#{options[:distro]}_#{options[:version]}-#{options[:arch]}" if a name wasn't specified
unless options[:name]
  options[:name] = "#{options[:distro]}_#{options[:version]}-#{options[:arch]}"
end

def build_headers options, ramdisk_id, kernel_id, type

  # These headers are required
  required_headers = {
    "x-image-meta-is-public" => "true",
  }

  if options[:storage] != nil
    required_headers = {"x-image-meta-store" => "#{options[:storage]}" }.merge required_headers
  end

  if type == "ramdisk"
    required_headers = { "x-image-meta-disk-format" => "ari", "x-image-meta-container-format" => "ari", "x-image-meta-name" => "#{options[:name]}-ramdisk" }.merge required_headers
  elsif type == "kernel"
    required_headers = { "x-image-meta-disk-format" => "aki", "x-image-meta-container-format" => "aki", "x-image-meta-name" => "#{options[:name]}-kernel" }.merge required_headers
  elsif type == "machine"
    required_headers = { "x-image-meta-disk-format" => "ami", "x-image-meta-container-format" => "ami" }.merge required_headers
  else
    puts "Something seems to be wrong... valid types are ramdisk, kernel or machine"
    exit 1
  end

  # If a ramdisk was included, we need to link the image to the ramdisk_id
  if ramdisk_id && type == "machine"
    required_headers = { "x-image-meta-property-ramdisk_id" => "#{ramdisk_id}" }.merge required_headers
  end

  # Same as above, except for the kernel
  if kernel_id && type == "machine"
    required_headers = { "x-image-meta-property-kernel_id" => "#{kernel_id}" }.merge required_headers
  end

  # These are the required options specific to ATT
  options_headers = {
    "x-image-meta-property-distro"      => "#{options[:distro]}",
    "x-image-meta-property-version"     => "#{options[:version]}",
    "x-image-meta-property-arch"        => "#{options[:arch]}"
  }

  # These are custom property headers. They're not required but if the user wants to add them, they can
  custom_headers = {}
  options[:custom].each do |custom|
    k,v = custom.split("=")
    custom_headers = { "x-image-meta-property-#{k}" => v }.merge custom_headers
  end

  # Finally we merge them all into one big hash and return it
  headers = {}
  headers.merge!(required_headers) if required_headers
  headers.merge!(options_headers) if options_headers
  headers.merge!(custom_headers) if custom_headers

end

def create options, ramdisk_id, kernel_id

  if options[:ramdisk] && ramdisk_id == ""
    # Upload the ramdisk and parse it's ID from the response
    @headers = build_headers options, ramdisk_id, kernel_id, "ramdisk"
    response = CONNECTION.image.create "#{options[:ramdisk]}", "#{options[:ramdisk]}", @headers
    ramdisk_id = response.id
  end

  if options[:kernel] && kernel_id == ""
    # Upload the kernel and parse it's ID from the response
    @headers = build_headers options, ramdisk_id, kernel_id, "kernel"
    response = CONNECTION.image.create "#{options[:kernel]}", "#{options[:kernel]}", @headers
    kernel_id = response.id
  end

  @headers = build_headers options, ramdisk_id, kernel_id, "machine"
  response = CONNECTION.image.create "#{options[:name]}", "#{options[:image]}", @headers
  return response
end

CONNECTION = Ogle::Client.new(
  :user => "#{options[:user]}",
  :pass => "#{options[:pass]}",
  :host => "#{options[:host]}",
  :port => "#{options[:port]}"
)

# If the argument specified in kernel and ramdisk are files that exist, upload them
if File.exist?("#{options[:kernel]}") && File.exist?("#{options[:ramdisk]}")
  response = create options, "", ""

# If the argument that was specified for ramdisk doesn't exist, and is an integer, then we assume it's a ramdisk_id and pass it along to create
elsif File.exist?("#{options[:kernel]}") && options[:ramdisk].to_i != 0
  response = create options, "#{options[:ramdisk]}", ""

# If the argument that was specified for kernel doesn't exist, and is an integer, then we assume it's a kernel_id and pass it alone to create
elsif File.exist?("#{options[:ramdisk]}") && options[:kernel].to_i != 0
  response = create options, "", "#{options[:kernel]}"

# If neither ramdisk nor kernel are on disk and they're both integers, then we pass them along to create to link up
elsif options[:ramdisk].to_i != 0 && options[:kernel].to_i != 0
  response = create options, "#{options[:ramdisk]}", "#{options[:kernel]}"
else
  if options[:kernel] == nil || options[:ramdisk] == nil
    response = create options, "", ""
  else
    puts "Something seems to have gone wrong, I'm out of here"
    exit 1
  end
end

if defined? response != "nil"
  puts response.inspect
end
