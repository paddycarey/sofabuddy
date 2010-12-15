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


import libsofabuddy
import os
import sys

from readconfig import *

if __name__ == "__main__":

    log = libsofabuddy.logging(log_file)
    episode_count = 0
    xbmc = libsofabuddy.send_xbmc_command(xbmc_ip, 9777)

    try:
        is_locked = open(lock_file)
    except:
        lock_up = open(lock_file,'w')
        for file_name in os.listdir(download_dir) :
            if not os.path.islink(os.path.join(download_dir, file_name)) and not os.path.isdir(os.path.join(download_dir, file_name)):
                try:
                    file_details = libsofabuddy.file_details(file_name, episode_number_regexes)
                except AttributeError as inst:
                    message = 'ERROR=Could not extract required data from filename FILE_NAME=' + os.path.join(download_dir, file_name) + ' ERRMSG=AttributeError: ' + str(inst)
                    log.output_log(message)
                except Exception as inst:
                    message = 'ERROR=Unknown error FILE_NAME=' + os.path.join(download_dir, file_name) + 'ERRMSG=' + str(type(inst)) + ' ' + str(inst)
                    log.output_log(message)
                else:
                    try:
                        episode_details = libsofabuddy.episode_details(file_details.show_name, file_details.season_no, file_details.episode_no)
                    except KeyError as inst:
                        message = 'ERROR=Could not find show or episode on tvrage.com FILE_NAME=' + os.path.join(download_dir, file_name) + ' ERRMSG=KeyError: ' + str(inst)
                        log.output_log(message)
                    except TypeError as inst:
                        message = 'ERROR=Network error FILE_NAME=' + os.path.join(download_dir, file_name) + ' ERRMSG=TypeError: ' + str(inst)
                        log.output_log(message)
                    except AttributeError as inst:
                        message = 'ERROR=Network error FILE_NAME=' + os.path.join(download_dir, file_name) + ' ERRMSG=AttributeError: ' + str(inst)
                        log.output_log(message)
                    except Exception as inst:
                        message = 'ERROR=Unknown error FILE_NAME=' + os.path.join(download_dir, file_name) + 'ERRMSG=' + str(type(inst)) + ' ' + str(inst)
                        log.output_log(message)
                    else:
                        file_operations = libsofabuddy.file_operations(episode_details.show_name, file_details.season_no, file_details.episode_no, episode_details.episode_title, file_details.quality, file_details.source, file_details.extension, download_dir, tv_dir, nuke_dir, file_name)
                        try:
                            nuke_info = file_operations.get_nuke_info()
                        except OSError:
                            pass
                        except NameError:
                            pass
                        except AttributeError:
                            pass
                        except Exception as inst:
                            message = 'ERROR=Unknown error FILE_NAME=' + os.path.join(download_dir, file_name) + 'ERRMSG=' + str(type(inst)) + ' ' + str(inst)
                            log.output_log(message)
                        else:
                            file_operations.do_nuke()
                            message = 'NUKESRC=' + nuke_info[0] + ' NUKEDST=' + nuke_info[1] + ' REASON=' + file_operations.nuke_reason
                            log.output_log(message)
                        file_operations.do_move()
                        episode_count = episode_count + 1
                        if os.path.isfile(file_operations.episode_path_new):
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
