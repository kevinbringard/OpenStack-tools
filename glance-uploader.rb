#!/usr/bin/env ruby

require 'ogle'
require 'optparse'

# Define our options
options = {}

optparse = OptionParser.new do |opts|
  opts.banner = "Usage: #{$0} -i|--image file -v|--version version -d|--distro distribution -a|--arch architecture [-H|--host host] [-p|--port port] [-n|--name name] [-r|-ramdisk ramdisk] [-k|--kernel kernel] [-e|--kernel_version kernel_version] [-c|--custom_fields field1=1,field2=2]"

  options[:host] = "localhost"
  opts.on( '-H', '--host HOST', 'Glance host to connect to (defaults to localhost)') do |host|
    options[:host] = host
  end

  options[:port] = "9292"
  opts.on( '-p', '--port PORT', 'Glance port to connect to (defaults to 9292)') do |port|
    options[:port] = port
  end

  options[:image] = nil
  opts.on( '-i', '--image FILE', 'Machine image to upload (required)') do |image|
    options[:image] = image
  end

  options[:name] = options[:image]
  opts.on( '-n', '--name NAME', 'Name to give the image when it has been uploaded (defaults to the image filename)') do |name|
    options[:name] = name
  end

  options[:ramdisk] = nil
  opts.on( '-r', '--ramdisk FILE', 'Ramdisk image to upload') do |ramdisk|
    options[:ramdisk] = ramdisk
  end

  options[:kernel] = nil
  opts.on( '-k', '--kernel FILE', 'Kernel image to upload') do |kernel|
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
  
  # These options are required
  unless options[:distro] && options[:version] && options[:arch]
    puts "You seem to be missing a required option"
    puts opts
    exit
  end
end

optparse.parse!

def build_headers options, ramdisk_id, kernel_id

  # These headers are required
  required_headers = {
    "x-image-meta-is-public"        => "true",
    "x-image-meta-name"             => "#{options[:name]}",
  }

  # If a ramdisk was included, we need to link the image to the ramdisk_id
  if ramdisk_id
    required_headers = { "x-image-meta-property-ramdisk_id" => "#{ramdisk_id}", "x-image-meta-disk-format" => "ari" }.merge required_headers
  end
  
  # Same as above, except for the kernel
  if kernel_id
    required_headers = { "x-image-meta-property-kernel_id" => "#{kernel_id}", "x-image-meta-container-format" => "aki" }.merge required_headers
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
  
  # Define done for recursion
  done = true
  if options[:ramdisk] && ! ramdisk_id
    # Upload the ramdisk and parse it's ID from the response
    @headers = build_headers options, ramdisk_id, kernel_id
    response = CONNECTION.image.create "#{options[:ramdisk]}", "#{options[:ramdisk]}", @headers
    ramdisk_id = response.id
    done = false
  end

  if options[:kernel] && ! kernel_id
    # Upload the kernel and parse it's ID from the response
    @headers = build_headers options, ramdisk_id, kernel_id
    response = CONNECTION.image.create "#{options[:kernel]}", "#{options[:kernel]}", @headers
    kernel_id = response.id
    done = false
  end

  @headers = build_headers options, ramdisk_id, kernel_id
  response = CONNECTION.image.create "#{options[:file]}", "#{options[:name]}", @headers

  unless done
    create options, ramdisk_id, kernel_id
  end
end

CONNECTION = Ogle::Client.new(
  :host => "#{options[:host]}",
  :port => "#{options[:port]}"
)
