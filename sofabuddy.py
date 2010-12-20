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
import logging
import os
import sys
import tvrage.exceptions

from readconfig import *

if __name__ == "__main__":

    logger = logging.getLogger("sofabuddy")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s", "%Y/%m/%d %H:%M:%S")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    if debugLogging:
        debugfh = logging.FileHandler(debugLogfile)
        debugfh.setLevel(logging.DEBUG)
        debugFormatter = logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s", "%Y/%m/%d %H:%M:%S")
        debugfh.setFormatter(debugFormatter)
        logger.addHandler(debugfh)

    episode_count = 0

    try:
        is_locked = open(lock_file)
    except:
        lock_up = open(lock_file,'w')
        message = 'Lock(' + lock_file + ')'
        logger.debug(message)
        for file_name in os.listdir(download_dir) :
            if not os.path.islink(os.path.join(download_dir, file_name)) and not os.path.isdir(os.path.join(download_dir, file_name)):
                try:
                    file_details = libsofabuddy.file_details(file_name, episode_number_regexes)
                except AttributeError as inst:
                    message = 'MetadataExtractionError(' + os.path.join(download_dir, file_name) + ')'
                    logger.error(message)
                except Exception as inst:
                    message = 'UnknownError(' + str(type(inst)) + ' ' + str(inst) + ') path(' + os.path.join(download_dir, file_name) + ')'
                    logger.critical(message)
                else:
                    try:
                        episode_details = libsofabuddy.episode_details(file_details.show_name, file_details.season_no, file_details.episode_no)
                    except KeyError as inst:
                        message = 'SeasonOrEpisodeNotFound(' + file_details.show_name + ', ' + file_details.season_no + ', ' + file_details.episode_no + ') path(' + os.path.join(download_dir, file_name) + ')'
                        logger.error(message)
                    except AttributeError as inst:
                        message = 'NetworkError(' + str(inst) + ')'
                        logger.warning(message)
                    except tvrage.exceptions.ShowNotFound as inst:
                        message = 'ShowNotFound(' + file_details.show_name + ') path(' + os.path.join(download_dir, file_name) + ')'
                        logger.error(message)
                    except Exception as inst:
                        message = 'UnknownError(' + str(type(inst)) + ' ' + str(inst) + ') path(' + os.path.join(download_dir, file_name) + ')'
                        logger.critical(message)
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
                            message = 'UnknownError(' + str(type(inst)) + ' ' + str(inst) + ') path(' + os.path.join(download_dir, file_name) + ')'
                            logger.critical(message)
                        else:
                            file_operations.do_nuke()
                        file_operations.do_move()
                        episode_count = episode_count + 1
        if episode_count > 0:
            xbmc = libsofabuddy.send_xbmc_command(xbmc_ip, 9777)
            xbmc.update_video_library()
        lock_up.close()
        os.remove(lock_file)
        message = 'Unlock(' + lock_file + ')'
        logger.debug(message)
    else:
        message = 'AlreadyLocked(' + lock_file + ')'
        logger.critical(message)
