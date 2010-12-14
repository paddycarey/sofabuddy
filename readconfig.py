#!/usr/bin/env python

#    readconfig.py - Script to parse command line options and a config file
#                    for use in sofabuddy.py
#
#    Copyright (C) 2010 Patrick Carey
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


#    Import required modules


import getopt
import sys

try:
    import config
except:
    sys.path.append('/etc/sofabuddy')
    import config

#    Function to display help message


def usage():
    print "sofabuddy.py [options]\n"
    print 'Example'
    print '\tsofabuddy.py -d "/media/downloads" -h "192.168.1.1"\n'
    print "Options"
    print "\t-?, --help\t\t\tWill bring up this message"
    print "\t-d, --download_dir\t\tOverride the default download directory"
    print "\t-n, --nuke_dir\t\t\tOverride the default nuke directory"
    print "\t-t, --tv_dir\t\t\tOverride the default tv directory"
    print "\t-l, --log_file\t\t\tChoose the location for your log file (default=/tmp/sofabuddy_log)"
    print "\t-k, --lock_file\t\t\tChoose the location for your lock file (default=/tmp/sofabuddy_lock)"
    print "\t-h, --host\t\t\tChoose the ip address of your XBMC box (default=127.0.0.1)"
    pass


#    Parse command line options


try:
    opts, args = getopt.getopt(sys.argv[1:], "?d:n:t:l:h:k:", ["help", "download_dir=", "nuke_dir=", "tv_dir=", "log_file=", "host=", "lock_file="])
except getopt.GetoptError, err:
    message = 'ERROR=sofabuddy.py: ' + str(err)
    print message
    usage()
    sys.exit(2)

for o, a in opts:
    if o in ("-?", "--help"):
        usage()
        sys.exit()
    if o in ("-d", "--download_dir"):
        download_dir = a
    elif o in ("-n", "--nuke_dir"):
        nuke_dir = a
    elif o in ("-t", "--tv_dir"):
        tv_dir = a
    elif o in ("-l", "--log_file"):
        log_file = a
    elif o in ("-k", "--lock_file"):
        lock_file = a
    elif o in ("-h", "--host"):
        xbmc_ip = a
    else:
        assert False, "unhandled option"


#    If option has not been set explicitly on the command line then check if it
#    has been set in the config file.


#    These options are required and do not have a default value set. The module
#    will throw an exception if a value for these variables cannot be obtained.


try:
    download_dir
except NameError:
    download_dir = config.download_dir

try:
    tv_dir
except NameError:
    tv_dir = config.tv_dir

try:
    nuke_dir
except NameError:
    nuke_dir = config.nuke_dir


#    These values are optional and if they are not specified then default
#    values will be used.


try:
    xbmc_ip
except NameError:
    try:
        xbmc_ip = config.xbmc_ip
    except AttributeError:
        xbmc_ip = '127.0.0.1'

try:
    log_file
except NameError:
    try:
        log_file = config.log_file
    except AttributeError:
        log_file = '/tmp/sofabuddy_log'
    
try:
    lock_file
except NameError:
    try:
        lock_file = config.lock_file
    except AttributeError:
        lock_file = '/tmp/sofabuddy_lock'


#    Read any advanced settings from config file if set, otherwise use default
#    values


try:
    episode_number_regexes = config.episode_number_regexes
except AttributeError:
    episode_number_regexes = [['s[0-9][0-9]e[0-9][0-9]', 1, 3, 4, 6], ['[0-9][0-9]x[0-9][0-9]', 0, 2, 3, 5], ['[0-9]x[0-9][0-9]', 0, 1, 2, 4], ['s[0-9][0-9] ep[0-9][0-9]', 1, 3, 6, 8]]
