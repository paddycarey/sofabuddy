#!/usr/bin/env python

import sys, re, os, string, tvrage.api

download_dir = '/media/somedir/downloads'
tv_dir = '/media/somedir/tv_library'
banner_dir = '/home/user/somedir'
nuke_dir = '/media/somedir/nuked'
lockfile = '/tmp/tvwrangler_lock'

def getfileinfo(filename):

    fileext = os.path.splitext(filename)
    results = re.search('s[0-9][0-9]e[0-9][0-9]', filename, re.I)
    sxxexx = results.group(0)
    snum = sxxexx[1:3]
    enum = sxxexx[4:6]
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
    epaired = str(episode.airdate)
    details = show.showid, show.name, snum, enum, epname, quality, fileext[1], filename, epaired
    log_line = show.name + ' [' + snum + 'x' + enum + '] ' + epname + ' [' + quality + ']' + fileext[1]
    print 'IDENTIFIED:', log_line, 'FILE:', filename
    return details


def do_file_move(showid, showname, snum, enum, epname, quality, fileext, origfilename, epaired):

    def find_relink(fullnukepath, nukemoveto):
      for x in os.listdir(download_dir):
        linkpath = os.path.join(download_dir, x)
        if os.path.islink(linkpath):
          if fullnukepath == os.readlink(linkpath):
            os.unlink(linkpath)
            os.symlink(nukemoveto, linkpath)
            break

    season_dir = 'Season ' + snum
    episode_filename = '[' + snum + 'x' + enum + ']' + ' ' + epname + ' [' + quality + ']' + fileext
    newpath = os.path.join(tv_dir, showname, season_dir, episode_filename)
    bannername = showname + '.jpg'
    showbanner = os.path.join(banner_dir, bannername)
    showdirbanner = os.path.join(tv_dir, showname, 'folder.jpg')
    seasondirbanner = os.path.join(tv_dir, showname, season_dir, 'folder.jpg')


    sdir = os.path.split(newpath)

    if not os.path.isdir(sdir[0]):
      os.renames(origfilename, newpath)
      os.symlink(newpath, origfilename)
      if not os.path.islink(seasondirbanner):
        os.symlink('../folder.jpg', seasondirbanner)
      if not os.path.islink(showdirbanner):
        os.symlink(showbanner, showdirbanner)
    else:
      for nukefile in os.listdir(sdir[0]):
        XXxXX = snum + 'x' + enum
        if nukefile.find(XXxXX) > 0:
          fullnukepath = os.path.join(sdir[0], nukefile)
          nukemoveto = os.path.join(nuke_dir, nukefile)
          nukemoveorigto = os.path.join(nuke_dir, origfilename)
          if quality == '1080P':
            os.renames(fullnukepath, nukemoveto)
            find_relink(fullnukepath, nukemoveto)
            print 'NUKE: NEW1080P', origfilename, fullnukepath
          elif quality == '720P' and nukefile.find('1080P') < 0:
            os.renames(fullnukepath, nukemoveto)
            find_relink(fullnukepath, nukemoveto)
            print 'NUKE: NEW720P', origfilename, fullnukepath
          elif nukefile.find('1080P') < 0 and nukefile.find('720P') < 0:
            os.renames(fullnukepath, nukemoveto)
            find_relink(fullnukepath, nukemoveto)
            print 'NUKE:', origfilename, fullnukepath
          else:
            os.renames(origfilename, nukemoveorigto)
            os.symlink(nukemoveorigto, origfilename)
            print 'NUKE: BETTERAVAIL', fullnukepath, origfilename
      if not os.path.islink(origfilename) and os.path.isfile(origfilename):
        os.renames(origfilename, newpath)
        os.symlink(newpath, origfilename)


if __name__ == "__main__":

    try:
      is_locked = open(lockfile)
      print 'ERROR: tvwrangler.py is locked'
    except:
      lockup = open(lockfile,'w')
      os.chdir(download_dir)
      for filename in os.listdir('.') :
        if not os.path.islink(filename) and not os.path.isdir(filename):
          try:
            episode_info = getfileinfo(filename)
            try:
              moveshit = do_file_move(episode_info[0], episode_info[1], episode_info[2], episode_info[3], episode_info[4], episode_info[5], episode_info[6], episode_info[7], episode_info[8])
            except:
              print 'ERROR: MOVE:', filename
          except:
            print 'ERROR: IDENTIFY:', filename
      lockup.close()
      os.remove(lockfile)
