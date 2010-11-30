#!/usr/bin/env python

#    tvwrangler.py - Auto sorter for tv episodes
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

import sys, re, os, shutil, string, tvrage.api, ConfigParser, time, datetime

config = ConfigParser.ConfigParser()
config.read('/etc/sofabuddy/config.cfg')

try:
    if os.path.isdir(sys.argv[1]):
        download_dir = sys.argv[1]
    else:
        print timestamp(), 'ERROR:', sys.argv[1], 'is not a directory. Using default.'
        download_dir = config.get('directories', 'download_dir')
except:
    download_dir = config.get('directories', 'download_dir')

tv_dir = config.get('directories', 'tv_dir')
nuke_dir = config.get('directories', 'nuke_dir')

lockfile = '/tmp/tvwrangler_lock'

def timestamp():
    return datetime.datetime.now().strftime("[%Y/%m/%d %H:%M:%S]")

def getfileinfo(filename):

    fileext = os.path.splitext(filename)
    results = re.search('s[0-9][0-9]e[0-9][0-9]', filename, re.I)
    try:
        sxxexx = results.group(0)
        snum = sxxexx[1:3]
        enum = sxxexx[4:6]
    except:
        try:
            results = re.search('[0-9][0-9]x[0-9][0-9]', filename, re.I)
            sxxexx = results.group(0)
            snum = sxxexx[0:2]
            enum = sxxexx[3:5]
        except:
            results = re.search('[0-9]x[0-9][0-9]', filename, re.I)
            sxxexx = results.group(0)
            snum_temp = sxxexx[0:1]
            snum = '0' + snum_temp
            enum = sxxexx[2:4]
    results2 = re.search('1080p|720p', filename, re.I)
    results3 = re.search('DVDRip|HDTV|PDTV|DSR|VHSRip', filename, re.I)
    if results2:
        qualityraw = results2.group(0)
        quality = string.upper(qualityraw)
    elif results3:
        qualityraw = results3.group(0)
        quality = string.upper(qualityraw)
    else:
        quality = 'TV'
    sss = '.*(?=%s)'
    showsearchstr = re.compile(sss % sxxexx)
    showsearch = showsearchstr.match(filename)
    showname = showsearch.group(0)
    cleanshowname = re.sub('\.', ' ', showname)
    show = tvrage.api.Show(cleanshowname)
    episode = show.season(int(snum)).episode(int(enum))
    rawepname = episode.title.encode("ascii", "replace")
    rawepname1 = re.sub('/', '-', rawepname)
    epname = re.sub('\?', '-', rawepname1)
    details = show.showid, show.name, snum, enum, epname, quality, fileext[1], filename
    log_line = show.name + ' [' + snum + 'x' + enum + '] ' + epname + ' [' + quality + ']' + fileext[1]
    print timestamp(), 'IDENTIFIED:', log_line, 'FILE:', filename
    return details


def find_relink(fullnukepath, nukemoveto):

    for x in os.listdir(download_dir):
        linkpath = os.path.join(download_dir, x)
        if os.path.islink(linkpath):
            if fullnukepath == os.readlink(linkpath):
                os.unlink(linkpath)
                os.symlink(nukemoveto, linkpath)
                break

def find_origfilename(fullnukepath):

    for x in os.listdir(download_dir):
        linkpath = os.path.join(download_dir, x)
        if os.path.islink(linkpath):
            if fullnukepath == os.readlink(linkpath):
                return x

def do_file_move(showid, showname, snum, enum, epname, quality, fileext, origfilename):

    season_dir = 'Season ' + snum
    episode_filename = '[' + snum + 'x' + enum + ']' + ' ' + epname + ' [' + quality + ']' + fileext
    newpath = os.path.join(tv_dir, showname, season_dir, episode_filename)

    sdir = os.path.split(newpath)

    if not os.path.isdir(sdir[0]):
        os.makedirs(sdir[0])
        shutil.move(origfilename, newpath)
        os.symlink(newpath, origfilename)
    else:
        for nukefile in os.listdir(sdir[0]):
            XXxXX = snum + 'x' + enum
            if nukefile.find(XXxXX) > 0:
                fullnukepath = os.path.join(sdir[0], nukefile)
                nuke_origfilename = find_origfilename(fullnukepath)
                if nuke_origfilename == 'None':
                    nukemoveto = os.path.join(nuke_dir, nukefile)
                else:
                    nukemoveto = os.path.join(nuke_dir, nuke_origfilename)
                nukemoveorigto = os.path.join(nuke_dir, origfilename)
                if quality == '1080P':
                    shutil.move(fullnukepath, nukemoveto)
                    find_relink(fullnukepath, nukemoveto)
                    print timestamp(), 'NUKE: NEW1080P', origfilename, fullnukepath
                elif quality == '720P' and nukefile.find('1080P') < 0:
                    shutil.move(fullnukepath, nukemoveto)
                    find_relink(fullnukepath, nukemoveto)
                    print timestamp(), 'NUKE: NEW720P', origfilename, fullnukepath
                elif nukefile.find('1080P') < 0 and nukefile.find('720P') < 0:
                    shutil.move(fullnukepath, nukemoveto)
                    find_relink(fullnukepath, nukemoveto)
                    print timestamp(), 'NUKE:', origfilename, fullnukepath
                else:
                    shutil.move(origfilename, nukemoveorigto)
                    os.symlink(nukemoveorigto, origfilename)
                    print timestamp(), 'NUKE: BETTERAVAIL', fullnukepath, origfilename
        if not os.path.islink(origfilename) and os.path.isfile(origfilename):
            shutil.move(origfilename, newpath)
            os.symlink(newpath, origfilename)


if __name__ == "__main__":

    try:
        is_locked = open(lockfile)
        print timestamp(), 'ERROR: tvwrangler.py is locked'
    except:
        lockup = open(lockfile,'w')
        os.chdir(download_dir)
        for filename in os.listdir('.') :
            if not os.path.islink(filename) and not os.path.isdir(filename):
                try:
                    episode_info = getfileinfo(filename)
                    try:
                        moveshit = do_file_move(episode_info[0], episode_info[1], episode_info[2], episode_info[3], episode_info[4], episode_info[5], episode_info[6], episode_info[7])
                    except Exception as inst:
                        print timestamp(), 'ERROR: MOVE:', "(", filename, ")", inst
                except Exception as inst:
                    print timestamp(), 'ERROR: IDENTIFY:', "(", filename, ")", inst
        lockup.close()
        os.remove(lockfile)
