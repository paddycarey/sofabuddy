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

    try:
        opts, args = getopt.getopt(sys.argv[1:], "d:")
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        sys.exit(2) 

    config = sofabuddy_functions.read_config('/etc/sofabuddy/test_config.cfg')

    download_dir = config.get_value('directories', 'download_dir')
    tv_dir = config.get_value('directories', 'tv_dir')
    nuke_dir = config.get_value('directories', 'nuke_dir')

    log_file = config.get_value('logging', 'log_file')

    log = sofabuddy_functions.logging(log_file)

    for file_name in os.listdir(download_dir) :
        if not os.path.islink(os.path.join(download_dir, file_name)) and not os.path.isdir(os.path.join(download_dir, file_name)):
            file_details = sofabuddy_functions.file_details(file_name)
            try:
                episode_details = sofabuddy_functions.episode_details(file_details.show_name, file_details.season_no, file_details.episode_no)
            except KeyError:
                message = 'ERROR=Could not find show or episode on tvrage.com FILE_NAME=' + file_name
                log.output_log(message)
            except TypeError:
                message = 'ERROR=Network error FILE_NAME=' + file_name
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
                    message = 'NUKESRC=' + nuke_info[0] + ' NUKEDST=' + nuke_info[1]
                    log.output_log(message)
                file_operations.do_move()
                message = 'MVSRC=' + file_operations.episode_path_old + ' MVDST=' + file_operations.episode_path_new
                log.output_log(message)
