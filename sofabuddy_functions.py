#!/usr/bin/env python

#    sofabuddy_functions.py - Useful functions for use in sofabuddy.py
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

import ConfigParser
import datetime
import os
import re
import shutil
import string
import tvrage.api

from socket import *
from xbmcclient import *

class logging:

    def __init__(self, log_file, log_level='1', log_mode='standard', time_format='[%Y/%m/%d %H:%M:%S]'):
        self.log_file = open(log_file,'a')
        self.log_level = log_level
        self.log_mode = log_mode
        self.time_format = time_format

    def timestamp(self):
        return datetime.datetime.now().strftime(self.time_format)

    def build_log_line(self):
        self.log_line = self.timestamp() + ' ' + self.message
        return self.log_line

    def output_log(self, message):
        self.message = message
        if not self.log_mode == 'cron':
            print self.build_log_line()
        log_line = self.build_log_line() + '\n' 
        self.log_file.write(log_line)

    def close_log(self):
        self.log_file.close()


class file_details:

    def __init__(self, file_name):
        self.file_name = file_name
        self.season_episode_no = self.season_episode_no()
        self.show_name = self.show_name()
        self.extension = self.extension()
        self.quality = self.quality()
        self.source = self.source()

    def show_name(self):
        show_name_regex = '.*(?=%s)'
        show_name_search_string = re.compile(show_name_regex % self.season_episode_no)
        show_search = show_name_search_string.match(self.file_name)
        raw_show_name = show_search.group(0)
        clean_show_name = re.sub('\.', ' ', raw_show_name)
        return string.rstrip(clean_show_name)

    def season_episode_no(self):
        regexes = [['s[0-9][0-9]e[0-9][0-9]', 1, 3, 4, 6], ['[0-9][0-9]x[0-9][0-9]', 0, 2, 3, 5], ['[0-9]x[0-9][0-9]', 0, 1, 2, 4]]
        for regex, season_start, season_end, episode_start, episode_end in regexes:
            results = re.search(regex, self.file_name, re.I)
            try:
                season_episode_no = results.group(0)
            except:
                pass
            else:
                self.season_no = season_episode_no[season_start:season_end]
                if len(self.season_no) == 1:
                    self.season_no = '0' + self.season_no
                self.episode_no = season_episode_no[episode_start:episode_end]
                if len(self.episode_no) == 1:
                    self.episode_no = '0' + self.episode_no
                return season_episode_no
                break

    def extension(self):
        extension = os.path.splitext(self.file_name)
        return extension[1]

    def quality(self):
        results = re.search('1080p|720p', self.file_name, re.I)
        if results:
            return string.upper(results.group(0))
        else:
            return 'SD'

    def source(self):
        results = re.search('bluray|brrip|hddvd|dvdrip|hdtv|pdtv|dsr|vhsrip', self.file_name, re.I)
        if results:
            return string.upper(results.group(0))
        else:
            return 'UNK'


class file_operations:

    def __init__(self, show_name, season_no, episode_no, episode_title, quality, source, extension, download_dir, tv_dir, nuke_dir, file_name):
        self.show_name = show_name
        self.season_no = season_no
        self.episode_no = episode_no
        self.episode_title = episode_title
        self.quality = quality
        self.source = source
        self.extension = extension
        self.download_dir = download_dir
        self.tv_dir = tv_dir
        self.nuke_dir = nuke_dir
        self.file_name = file_name
        self.prepare_strings()

    def prepare_strings(self):
        self.season_dir = 'Season ' + self.season_no
        self.episode_filename_old = self.file_name
        self.episode_path_old = os.path.join(self.download_dir, self.episode_filename_old)
        self.episode_filename_new = '[' + self.season_no + 'x' + self.episode_no + ']' + ' ' + self.episode_title + ' [' + self.quality + '][' + self.source + ']' + self.extension
        self.episode_path_new = os.path.join(self.tv_dir, self.show_name, self.season_dir, self.episode_filename_new)
        self.episode_dir_new = os.path.join(self.tv_dir, self.show_name, self.season_dir)

    def get_nuke_info(self):
        for nukefile in os.listdir(self.episode_dir_new):
            XXxXX = self.season_no + 'x' + self.episode_no
            if nukefile.find(XXxXX) > 0:
                self.episode_to_be_nuked = os.path.join(self.episode_dir_new, nukefile)
                self.nuke_file_name_new = ''
                for x in os.listdir(self.download_dir):
                    link_path = os.path.join(self.download_dir, x)
                    if os.path.islink(link_path):
                        if self.episode_to_be_nuked == os.readlink(link_path):
                            self.nuke_file_name_new = x
                if self.nuke_file_name_new == '':
                    self.nuke_file_name_new = nukefile
                self.nuke_path_new = os.path.join(self.nuke_dir, self.nuke_file_name_new)
                if self.quality == '1080P':
                    self.nuke_reason = 'NEWIS1080P'
                elif self.quality == '720P' and nukefile.find('1080P') < 0:
                    self.nuke_reason = 'NEWIS720P'
                elif nukefile.find('1080P') < 0 and nukefile.find('720P') < 0:
                    self.nuke_reason = 'NEWERDL'
                else:
                    self.nuke_reason = 'BETTERAVAIL'
                    self.episode_to_be_nuked = os.path.join(self.download_dir, self.file_name)
                    self.nuke_path_new = os.path.join(self.nuke_dir, self.file_name)

    def find_relink(self):
        for x in os.listdir(self.download_dir):
            link_path = os.path.join(self.download_dir, x)
            if os.path.islink(link_path):
                if self.episode_to_be_nuked == os.readlink(link_path):
                    os.unlink(link_path)
                    os.symlink(self.nuke_path_new, link_path)
                    break

    def do_nuke(self):
        shutil.move(self.episode_to_be_nuked, self.nuke_path_new)
        self.find_relink()

    def do_move(self):
        if not os.path.isdir(self.episode_dir_new):
            os.makedirs(self.episode_dir_new)
        if not os.path.islink(episode_path_old) and os.path.isfile(self.episode_path_old):
            shutil.move(self.episode_path_old, self.episode_path_new)
            os.symlink(self.episode_path_new, self.episode_path_old)


class episode_details:

    def __init__(self, showname, season_no, episode_no):
        self.show = tvrage.api.Show(showname)
        self.show_name = self.show.name
        self.episode = self.show.season(int(season_no)).episode(int(episode_no))
        self.episode_title = re.sub('/', '-', self.episode.title)
        self.episode_title = re.sub('\?', '-', self.episode_title)


class read_config:

    def __init__(self, config_file):
        self.config = ConfigParser.ConfigParser()
        self.config.read(config_file)

    def get_value(self, section, value):
        self.config_value = self.config.get(section, value)
        return self.config_value


class send_xbmc_command:
    
    def __init__(self, ip, port):
        self.addr = (ip, port)
        self.sock = socket(AF_INET,SOCK_DGRAM)
    
    def update_video_library(self):
        packet = PacketACTION(actionmessage="XBMC.updatelibrary(video)", actiontype=ACTION_BUTTON)
        packet.send(self.sock, self.addr)
