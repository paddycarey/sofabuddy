#!/usr/bin/env python

#    sofabuddy.py - TV Episode Manager
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

import sofabuddy_functions
import os
import sys
import getopt

def usage():
    print "sofabuddy.py [options]"
    print 'Example'
    print '\tsofabuddy.py -d "/media/downloads" -h "192.168.1.1"'
    print "Options"
    print "\t-?, --help\t\t\tWill bring up this message"
    print "\t-d, --download_dir\t\tOverride the default download directory"
    print "\t-n, --nuke_dir\t\t\tOverride the default nuke directory"
    print "\t-t, --tv_dir\t\t\tOverride the default tv directory"
    print "\t-l, --log_file\t\t\tChoose the location for your log file (default=/tmp/sofabuddy_log)"
    print "\t-h, --host=HOST\t\t\tChoose the ip address of your XBMC box (default=127.0.0.1)"
    pass


if __name__ == "__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:], "?d:n:t:l:h:", ["help", "download_dir=", "nuke_dir=", "tv_dir=", "log_file=", "host="])
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
        if o in ("-t", "--tv_dir"):
            tv_dir = a
        if o in ("-l", "--log_file"):
            log_file = a
        elif o in ("-h", "--host"):
            xbmc_ip = a
        else:
            assert False, "unhandled option"

    try:
        config = sofabuddy_functions.read_config('/etc/sofabuddy/config.cfg')
    except:
        pass
    else:
        try:
            log_file
        except NameError:
            try:
                log_file = config.get_value('logging', 'log_file')
            except:
                log_file = '/tmp/sofabuddy_log'
        try:
            download_dir
        except NameError:
            download_dir = config.get_value('directories', 'download_dir')
        try:
            tv_dir
        except NameError:
            tv_dir = config.get_value('directories', 'tv_dir')
        try:
            nuke_dir
        except NameError:
            nuke_dir = config.get_value('directories', 'nuke_dir')
        try:
            xbmc_ip
        except NameError:
            try:
                xbmc_ip = config.get_value('xbmc', 'ip')
            except:
                xbmc_ip = '127.0.0.1'

    log = sofabuddy_functions.logging(log_file)
    lock_file = '/tmp/sofabuddy_lock'
    episode_count = 0
    xbmc = sofabuddy_functions.send_xbmc_command(xbmc_ip, 9777)

    try:
        is_locked = open(lock_file)
    except:
        lock_up = open(lock_file,'w')
        for file_name in os.listdir(download_dir) :
            if not os.path.islink(os.path.join(download_dir, file_name)) and not os.path.isdir(os.path.join(download_dir, file_name)):
                try:
                    file_details = sofabuddy_functions.file_details(file_name)
                except AttributeError as inst:
                    message = 'ERROR=Could not extract required data from filename FILE_NAME=' + file_name + ' ERRMSG=AttributeError: ' + str(inst)
                    log.output_log(message)
                except Exception as inst:
                    message = 'ERROR=Unknown error FILE_NAME=' + file_name + 'ERRMSG=' + str(type(inst)) + ' ' + str(inst)
                    log.output_log(message)
                else:
                    try:
                        episode_details = sofabuddy_functions.episode_details(file_details.show_name, file_details.season_no, file_details.episode_no)
                    except KeyError as inst:
                        message = 'ERROR=Could not find show or episode on tvrage.com FILE_NAME=' + file_name + ' ERRMSG=KeyError: ' + str(inst)
                        log.output_log(message)
                    except TypeError as inst:
                        message = 'ERROR=Network error FILE_NAME=' + file_name + ' ERRMSG=TypeError: ' + str(inst)
                        log.output_log(message)
                    except AttributeError as inst:
                        message = 'ERROR=Network error FILE_NAME=' + file_name + ' ERRMSG=AttributeError: ' + str(inst)
                        log.output_log(message)
                    except Exception as inst:
                        message = 'ERROR=Unknown error FILE_NAME=' + file_name + 'ERRMSG=' + str(type(inst)) + ' ' + str(inst)
                        log.output_log(message)
                    else:
                        file_operations = sofabuddy_functions.file_operations(episode_details.show_name, file_details.season_no, file_details.episode_no, episode_details.episode_title, file_details.quality, file_details.source, file_details.extension, download_dir, tv_dir, nuke_dir, file_name)
                        try:
                            nuke_info = file_operations.get_nuke_info()
                        except OSError:
                            pass
                        except NameError:
                            pass
                        except AttributeError:
                            pass
                        except Exception as inst:
                            message = 'ERROR=Unknown error FILE_NAME=' + file_name + 'ERRMSG=' + str(type(inst)) + ' ' + str(inst)
                            log.output_log(message)
                        else:
                            file_operations.do_nuke()
                            message = 'NUKESRC=' + nuke_info[0] + ' NUKEDST=' + nuke_info[1] + ' REASON=' + file_operations.nuke_reason
                            log.output_log(message)
                        file_operations.do_move()
                        episode_count = episode_count + 1
                        message = 'MVSRC=' + file_operations.episode_path_old + ' MVDST=' + file_operations.episode_path_new
                        log.output_log(message)
        if episode_count > 0:
            xbmc.update_video_library()
            message = 'XBMC=Updating video library IP=' + xbmc_ip
            log.output_log(message)
        lock_up.close()
        os.remove(lock_file)
    else:
        message = 'ERROR=sofabuddy.py is locked'
        log.output_log(message)
