#!/usr/bin/env python

###############################################################################
#   These are required variables, although they can also be set on the command
#   line if you wish. sofabuddy.py will not run if these variables are not set.
###############################################################################

#   The location of your tv episodes to be sorted
download_dir = '/media/some_dir/downloads'

#   The location of your tv library
tv_dir = '/media/some_dir/tv_library'

#   The location that nuked files should be moved to
nuke_dir = '/media/some_dir/nuked'

###############################################################################
#   These variables are optional. sofabuddy will use default values if they are
#   not set.  You can uncomment each one to enable it as needed.
###############################################################################

#   The ip address or hostname of your xbmc box to send update commands to
#xbmc_ip = '127.0.0.1'

#   The location of the sofabuddy log file
#log_file = '/tmp/sofabuddy.log'

#   The location of the sofabuddy lock file
#lock_file = '/tmp/sofabuddy.lock'

###############################################################################
#   Advanced config options. Only change if you know what you are doing
###############################################################################

#   Turn debug logging on by uncommenting this variable
#debug_logging = 1

#   You can set the location of your debug log by modifying this string
#debug_logfile = '/tmp/sofabuddy.debug.log'

#   You can modify the format of your output filenames by editing the string
#   below.  Possible values are:
#   ${showName} = Show title as found on tvrage.com
#   ${seasonNumber} = Season number
#   ${episodeNumber} = Episode number
#   ${episodeTitle} = Episode title as found on tvrage.com
#   ${quality} =  Quality of the file e.g. SD, 720P or 1080P
#   ${source} = Source of the file e.g. HDTV, BluRay, DSRip etc.
#   ${extension} = File extension e.g. mkv, avi, m2ts etc.
#new_filename_format = '[${seasonNumber}x${episodeNumber}] ${episodeTitle} [${quality}][${source}].${extension}'

#   You can add additional regexes to this list to recognise more season and
#   episode number formats
#episode_number_regexes = [['s[0-9][0-9]e[0-9][0-9]', 1, 3, 4, 6], ['[0-9][0-9]x[0-9][0-9]', 0, 2, 3, 5], ['[0-9]x[0-9][0-9]', 0, 1, 2, 4], ['s[0-9][0-9] ep[0-9][0-9]', 1, 3, 6, 8]]
