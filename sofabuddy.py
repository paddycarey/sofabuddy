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
import readconfig
import sb_exceptions
import sys
import time
import tvrage.exceptions

from httplib import IncompleteRead

class sofabuddy:

    def __init__(self):
        self.logger = logging.getLogger("sofabuddy")
        self.logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(readconfig.log_file)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s", "%Y/%m/%d %H:%M:%S")
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        consoleFormatter = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s", "%Y/%m/%d %H:%M:%S")
        ch.setFormatter(consoleFormatter)
        self.logger.addHandler(ch)


        if readconfig.debug_logging:
            debugfh = logging.FileHandler(readconfig.debug_logfile)
            debugfh.setLevel(logging.DEBUG)
            debugFormatter = logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s", "%Y/%m/%d %H:%M:%S")
            debugfh.setFormatter(debugFormatter)
            self.logger.addHandler(debugfh)

        self.episode_count = 0
        self.ignore_queue = []

    def process_file(self, download_dir, file_name):
        if not os.path.splitext(file_name)[1] == '.mkv' and not os.path.splitext(file_name)[1] == '.avi' and not os.path.splitext(file_name)[1] == '.mpg':
            message = 'Not a video file \"' + file_name + '\"'
            error_string = 'FileNotVideoError'
            self.manage_log_spam(download_dir, file_name, error_string, message)
        else:
            try:
                file_details = libsofabuddy.file_details(file_name, readconfig.episode_number_regexes)
            except sb_exceptions.SeasonOrEpisodeNoNotFound as inst:
                message = 'Could not extract season or episode number from \"' + os.path.join(download_dir, file_name) + '\"'
                error_string = str(type(inst)) + str(inst)
                self.manage_log_spam(download_dir, file_name, error_string, message)
                message = 'SeasonOrEpisodeNoNotFound=\"' + os.path.join(download_dir, file_name) + '\"'
                self.manage_log_spam(download_dir, file_name, error_string, message)
            except sb_exceptions.ShowNameNotFound as inst:
                message = 'Could not extract show name from \"' + os.path.join(download_dir, file_name) + '\"'
                error_string = str(type(inst)) + str(inst)
                self.manage_log_spam(download_dir, file_name, error_string, message)
                message = 'ShowNameNotFound=\"' + os.path.join(download_dir, file_name) + '\"'
                self.manage_log_spam(download_dir, file_name, error_string, message)
            else:
                try:
                    episode_details = libsofabuddy.episode_details(file_details.show_name, file_details.season_no, file_details.episode_no)
                except KeyError as inst:
                    message = 'Could not find episode on tvrage.com \"' + file_details.show_name + ' ' + file_details.season_no + 'x' + file_details.episode_no + '\"'
                    error_string = str(type(inst)) + str(inst)
                    self.manage_log_spam(download_dir, file_name, error_string, message)
                    message = 'KeyError=\"' + file_details.show_name + ' ' + file_details.season_no + 'x' + file_details.episode_no + '\"'
                    self.manage_log_spam(download_dir, file_name, error_string, message)
                except (AttributeError, IncompleteRead) as inst:
                    message = 'Could not retrieve data for \"' + file_details.show_name + ' ' + file_details.season_no + 'x' + file_details.episode_no + '\"'
                    error_string = str(type(inst)) + str(inst)
                    self.manage_log_spam(download_dir, file_name, error_string, message)
                    message = 'NetworkError=\"' + str(inst) + '\"'
                    self.manage_log_spam(download_dir, file_name, error_string, message)
                except TypeError as inst:
                    message = 'Found show but not season on tvrage.com \"' + file_details.show_name + '\"'
                    error_string = str(type(inst)) + str(inst)
                    self.manage_log_spam(download_dir, file_name, error_string, message)
                    message = 'SeasonNotFound=\"' + file_details.show_name + '\"'
                    error_string = str(type(inst)) + str(inst)
                    self.manage_log_spam(download_dir, file_name, error_string, message)
                except tvrage.exceptions.ShowNotFound as inst:
                    message = 'Could not find show on tvrage.com \"' + file_details.show_name + '\"'
                    error_string = str(type(inst)) + str(inst)
                    self.manage_log_spam(download_dir, file_name, error_string, message)
                    message = 'ShowNotFound=\"' + file_details.show_name + '\"'
                    error_string = str(type(inst)) + str(inst)
                    self.manage_log_spam(download_dir, file_name, error_string, message)
                else:
                    file_operations = libsofabuddy.file_operations(episode_details.show_name, file_details.season_no, file_details.episode_no, episode_details.episode_title, file_details.quality, file_details.source, file_details.extension, download_dir, readconfig.tv_dir, readconfig.nuke_dir, file_name)
                    try:
                        nuke_info = file_operations.get_nuke_info()
                    except (OSError, NameError, AttributeError):
                        pass
                    else:
                        file_operations.do_nuke()
                    file_operations.do_move()
                    self.episode_count = self.episode_count + 1

    def manage_log_spam(self, download_dir, file_name, error_string, message):
        if not [[download_dir, file_name], error_string] in self.ignore_queue:
            self.logger.error(message)
            self.ignore_queue = self.ignore_queue + [[[download_dir, file_name], error_string]]
        else:
            self.logger.debug(message)

    def update_xbmc(self):
        if self.episode_count > 0:
            xbmc = libsofabuddy.send_xbmc_command(readconfig.xbmc_ip, 9777)
            xbmc.update_video_library()
            self.episode_count = 0
            time.sleep(60)

    def do_sleep(self):
        sleepcount = 0
        while sleepcount < readconfig.sleep_time:
            if not os.path.isfile(readconfig.sleep_interrupt):
                time.sleep(1)
                sleepcount = sleepcount + 1
            else:
                message = 'Caught interrupt'
                self.logger.debug(message)
                os.remove(readconfig.sleep_interrupt)
                break

    def generate_dir_list(self, download_dir, recursive):
        self.dir_list = []
        if recursive:
            for x in os.walk(download_dir):
                self.dir_list = self.dir_list + [x[0]]
        else:
            self.dir_list = [download_dir]

    def sofabuddy_header():
        message = 'Starting sofabuddy.py'
        self.logger.debug(message)
        message = ''
        self.logger.debug(message)

if __name__ == "__main__":

    sb = sofabuddy()

    try:
        is_locked = open(readconfig.lock_file)
    except:
        lock_up = open(readconfig.lock_file,'w')
        message = 'Locking sofabuddy.py \"' + readconfig.lock_file + '\"'
        sb.logger.debug(message)
        while True:
            sb.generate_dir_list(readconfig.download_dir, readconfig.recursive)
            try:
                for download_dir in sb.dir_list:
                    for file_name in os.listdir(download_dir) :
                        if not os.path.islink(os.path.join(download_dir, file_name)) and not os.path.isdir(os.path.join(download_dir, file_name)):
                            sb.process_file(download_dir, file_name)
                sb.update_xbmc()
                sb.do_sleep()
            except KeyboardInterrupt:
                lock_up.close()
                os.remove(readconfig.lock_file)
                message = 'Unlocking sofabuddy.py: KeyboardInterrupt'
                sb.logger.debug(message)
                sys.exit(2)
            except:
                lock_up.close()
                os.remove(readconfig.lock_file)
                message = 'Unknown error encountered: please file a ticket.'
                sb.logger.exception(message)
                sys.exit(2)

    else:
        message = 'sofabuddy.py is already locked \"' + readconfig.lock_file + '\"'
        sb.logger.critical(message)
