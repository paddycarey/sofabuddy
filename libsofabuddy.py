#!/usr/bin/env python

#    libsofabuddy.py - Useful functions for use in sofabuddy.py
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

import datetime
import logging
import os
import re
import sb_exceptions
import shutil
import string
import tvrage.api

from tvrage.exceptions import *
from socket import *
from xbmcclient import *

logger = logging.getLogger("sofabuddy.libsofabuddy")

class file_details:

    def __init__(self, file_name, regexes):
        self.logger = logging.getLogger("sofabuddy.libsofabuddy.file_details")
        logMessage = 'file_details instance initialised'
        self.logger.debug(logMessage)
        self.file_name = file_name
        logMessage = 'file_name=\"' + self.file_name + '\"'
        self.logger.debug(logMessage)
        self.regexes = regexes
        self.season_episode_no = self.season_episode_no()
        try:
            logMessage = 'season_episode_no=\"' + self.season_episode_no + '\"'
        except TypeError:
            raise sb_exceptions.SeasonOrEpisodeNoNotFound(self.file_name)
        self.logger.debug(logMessage)
        self.show_name = self.show_name()
        logMessage = 'show_name=\"' + self.show_name + '\"'
        self.logger.debug(logMessage)
        self.extension = self.extension()
        logMessage = 'extension=\"' + self.extension + '\"'
        self.logger.debug(logMessage)
        self.quality = self.quality()
        logMessage = 'quality=\"' + self.quality + '\"'
        self.logger.debug(logMessage)
        self.source = self.source()
        logMessage = 'source=\"' + self.source + '\"'
        self.logger.debug(logMessage)

    def show_name(self):
        show_name_regex = '.*(?=%s)'
        show_name_search_string = re.compile(show_name_regex % self.season_episode_no)
        show_search = show_name_search_string.match(self.file_name)
        raw_show_name = show_search.group(0)
        clean_show_name = re.sub('\.', ' ', raw_show_name)
        clean_show_name = re.sub('\[', ' ', clean_show_name)
        clean_show_name = string.rstrip(clean_show_name)
        if len(clean_show_name) > 1:
            return clean_show_name
        else:
            raise sb_exceptions.ShowNameNotFound(self.file_name)

    def season_episode_no(self):
        for regex, season_start, season_end, episode_start, episode_end in self.regexes:
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
                logMessage = 'regex_matched=\"' + str(regex) + '\"'
                self.logger.debug(logMessage)
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
        self.logger = logging.getLogger("sofabuddy.libsofabuddy.file_operations")
        logMessage = 'file_operations instance initialised'
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
                break
        return [self.episode_to_be_nuked, self.nuke_path_new]

    def find_relink(self):
        for x in os.listdir(self.download_dir):
            link_path = os.path.join(self.download_dir, x)
            if os.path.islink(link_path):
                if self.episode_to_be_nuked == os.readlink(link_path):
                    os.unlink(link_path)
                    logMessage = 'nukeOrigFilename=\"' + link_path + '\"'
                    self.logger.debug(logMessage)
                    os.symlink(self.nuke_path_new, link_path)
                    break

    def do_nuke(self):
        shutil.move(self.episode_to_be_nuked, self.nuke_path_new)
        logMessage = 'NukeSrc=\"' + self.episode_to_be_nuked + '\"'
        self.logger.info(logMessage)
        logMessage = 'NukeDest=\"' + self.nuke_path_new + '\"'
        self.logger.info(logMessage)
        logMessage = 'NukeReason=\"' + self.nuke_reason + '\"'
        self.logger.info(logMessage)
        if self.nuke_reason == 'BETTERAVAIL':
            os.symlink(self.nuke_path_new, self.episode_to_be_nuked)
        else:
            self.find_relink()

    def do_move(self):
        if not os.path.isdir(self.episode_dir_new):
            os.makedirs(self.episode_dir_new)
        if not os.path.islink(self.episode_path_old):
            if os.path.isfile(self.episode_path_old):
                shutil.move(self.episode_path_old, self.episode_path_new)
                logMessage = 'Processed \"' + self.episode_path_old + '\" Show Name \"' + self.show_name + '\" Episode \"' + self.season_no + 'x' + self.episode_no + ' ' + self.episode_title + '\" Quality \"' + self.quality + '\"'
                self.logger.info(logMessage)
                os.symlink(self.episode_path_new, self.episode_path_old)


class episode_details:

    def __init__(self, showname, season_no, episode_no):
        self.logger = logging.getLogger("sofabuddy.libsofabuddy.episode_details")
        logMessage = 'episode_details instance initialised'
        self.logger.debug(logMessage)
        self.show = tvrage.api.Show(showname)
        self.show_name = self.show.name
        self.episode = self.show.season(int(season_no)).episode(int(episode_no))
        self.episode_title = self.episode.title.encode("ascii", "replace")
        self.episode_title = re.sub('/', '-', self.episode_title)
        self.episode_title = re.sub('\?', '-', self.episode_title)
        logMessage = 'show_name=\"' + self.show_name + '\"'
        self.logger.debug(logMessage)
        logMessage = 'episode_title=\"' + self.episode_title + '\"'
        self.logger.debug(logMessage)

class send_xbmc_command:

    def __init__(self, ip, port):
        self.logger = logging.getLogger("sofabuddy.libsofabuddy.send_xbmc_command")
        logMessage = 'send_xbmc_command instance initialised'
        self.logger.debug(logMessage)
        self.addr = (ip, port)
        self.sock = socket(AF_INET,SOCK_DGRAM)

    def update_video_library(self):
        logMessage = 'updateVideoLibrary=\"' + str(self.addr) + '\"'
        self.logger.debug(logMessage)
        packet = PacketACTION(actionmessage="XBMC.updatelibrary(video)", actiontype=ACTION_BUTTON)
        packet.send(self.sock, self.addr)
