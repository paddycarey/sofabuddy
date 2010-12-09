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

if __name__ == "__main__":

    config = sofabuddy_functions.read_config('/etc/sofabuddy/config.cfg')
    log_file = config.get_value('logging', 'log_file')
    log = sofabuddy_functions.logging(log_file)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "dh:", ["download_dir=", "host="])
    except getopt.GetoptError, err:
        message = 'ERROR=sofabuddy.py: ' + str(err)
        log.output_log(message)
        sys.exit(2) 

    download_dir = config.get_value('directories', 'download_dir')
    tv_dir = config.get_value('directories', 'tv_dir')
    nuke_dir = config.get_value('directories', 'nuke_dir')

    try:
        xbmc_ip = config.get_value('xbmc', 'ip')
    except:
        xbmc_ip = '127.0.0.1'

    lock_file = '/tmp/tvwrangler_lock'
    episode_count = 0
    xbmc = sofabuddy_functions.send_xbmc_command(xbmc_ip)

    for o, a in opts:
        if o in ("-d", "--download_dir"):
            download_dir = a
        elif o in ("-h", "--host"):
            xbmc_ip = a
        else:
            assert False, "unhandled option" 

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
            message = 'XBMC: update_video_library()'
            log.output_log(message)
        lock_up.close()
        os.remove(lock_file)
    else:
        message = 'ERROR=sofabuddy.py is locked'
        log.output_log(message)
