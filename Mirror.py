#!/usr/bin/python
#-*- coding: utf-8 -*-
# vim:ts=4:expandtab
# (c) Jerzy Kędra 2013-2014
# Python 2.7
""" Mirror.py : Mirror a podcast to local resource.
    This script is intendent to be run daily from cron,
    and copy incoming podcasts into a local directory.
    Primarily designed to mirror Daily Audio Biblle podcasts,
    after I have got caught with missing podcasts with end of
    the year, when Brian Hardin (podcast autor) removed the old
    podcasts and started a new yearly cycle.
    Default config: mirror.cfg
    Config properites:
    
    TODO: limit max nr of podcasts downloaded in one pass.
"""

import os
import sys
import urllib2
import urllib
import httplib
from BeautifulSoup import BeautifulSoup, Tag, BeautifulStoneSoup
#from datetime import datetime
import email.utils as eut
import datetime
#
import codecs
from urlparse import urlparse
import shutil
import argparse
import logging
import ConfigParser
import UserDict


class PodcastURLopener(urllib.FancyURLopener):
    """Create sub-class in order to overide error 206.
    
       The error means a partial file is being sent,
       which is ok in this case.
       Do nothing with this error.
    """
    
    def http_error_206(self, url, fp, errcode, errmsg, headers, data=None):
        pass

def reporthook(blocks_read, block_size, total_size):
    """Print progress. It is an argument to urlretrieve."""
    total_size = pi.size

    if not blocks_read:
        return
    if total_size < 0:
        # Unknown size
        print ' Read %d blocks' % blocks_read
    else:
        amount_read = blocks_read * block_size + pi.siz3
        print ' Read ',
        if amount_read < 1024*1024:
            print '%dkB ' % (amount_read/1024),
        elif amount_read > 1024*1024:
            print '%dMB ' % (amount_read/1024/1024),

        print '%d%%    \r' % (100*amount_read/total_size),
    return


# returns size of the http object, follows redirs
def getsize(url):
    """Return Content-Length value for given URL. Follow redirs."""
    o = urlparse(url)
    conn = httplib.HTTPConnection(o.netloc)
    conn.request("HEAD", o.path)
    res = conn.getresponse()

    # https://docs.python.org/2/library/httplib.html
    statuses = (httplib.MOVED_PERMANENTLY, httplib.FOUND)
    if res.status in statuses:
        # print res.reason, ": ", res.getheader('location')
        return getsize(res.getheader('location'))
    elif res.status == httplib.OK:
        # inne interesujace tagi: etag
        return res.getheader('content-length')
    else:
        log.warn("getsize() UNKNOWN PROBLEM")
        log.warn("{}: {} ".format(res.reason, res.getheader('location')))
        log.warn(res.getheaders())
        raise IOError

def descwrite(i):
    """Write a description in a file for given podcast."""
    podnm = i.title.string
    f = codecs.open(pi.ftxt, encoding='utf-8', mode='w')

    f.write(podnm)
    f.write("\n\n")
    # enclosing in try-exception because of this error
    # TypeError: coercing to Unicode: need string or buffer, Tag found
    try:
        # This is to decode &lt/&gt before writing it to the file
        # BeautifulStoneSoup(items[1].description.string,
        #       convertEntities=BeautifulStoneSoup.HTML_ENTITIES).contents[0]
        f.write(BeautifulStoneSoup(i.description.string,
                                convertEntities=
                                BeautifulStoneSoup.HTML_ENTITIES).contents[0])
    except TypeError:
        f.write(i.description.string)

def initLog(log, args):
    """Initialize logging system"""
    log_levels = { None : logging.WARN,
                   1 : logging.INFO,
                   2 : logging.DEBUG }
                   
    log.setLevel(log_levels[args.verbose])
    
    if args.logfile:
        chnLog = logging.FileHandler(args.logfile, mode='a')
        chnLog.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s"))
        log.addHandler(chnLog)

    if not args.silent:
        # create console handler and set level to debug
        chnStr = logging.StreamHandler()
        chnStr.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
        log.addHandler(chnStr)

def initParser():
    p = argparse.ArgumentParser()
    p.add_argument("-v", "--verbose", action="count",
                        help="increases verbosity")
    p.add_argument("-d", "--days", type=int, default=30,
                        help="how far in the past go")
    p.add_argument("-t", "--target", default="DATA",
                        help="target data directory")
    p.add_argument("-l", "--logfile",
                        help="logging to file, log file path required")
    p.add_argument("-s", "--silent", action="store_true",
                        help="silent mode - suppress terminal output")
    return p.parse_args()

class PodcastItem:
    """ 
        Parses and stores BeautifulSoup.Tag information.
    """
    def __init__(self, item):
        if type(item) is not Tag:
            return
        self.name = item.title.string
        self.date = datetime.datetime(*eut.parsedate(item.pubdate.string)[:6])
        self.fmp3 = self.name + '.mp3'
        self.tmp3 = self.name + '.mp3.part'
        self.ftxt = self.name + '.txt'
        self.url = item.find('media:content')['url']
        self.siz3 = 0
        self.size = 0

# MAIN PROGRAM STARTS HERE

args = initParser()
log = logging.getLogger(__name__)
initLog(log, args)

config = ConfigParser.ConfigParser()
cf=config.read(['mirror.cfg', os.path.expanduser('~/.mirror.cfg')])
if len(cf)==0:
    print "config file not found"
    sys.exit(-1)
else:
    log.debug("config file %s" % str(cf))
    
baseurl = config.get("RSS", "baseurl")

current_page = urllib2.urlopen(baseurl)
soup = BeautifulSoup(current_page)

if not os.path.isdir(args.target):
    os.makedirs(args.target)
log.debug("changing dir to {}".format(args.target))
os.chdir(args.target)


for i in soup.findAll('item'):
    pi = PodcastItem(i)

    podcast_age = datetime.datetime.now() - pi.date
    if podcast_age > datetime.timedelta(days=args.days):
        log.debug("{} too old".format(pi.name, pi.date))
        continue

    # sprawdźmy czy plik w ogóle da się ściągnąć
    # jak nie - iterujemy od początku
    try:
        pi.size = int(getsize(pi.url))
    except (IOError, TypeError) as e:
        continue

    # write description to description file
    if not os.path.exists(pi.ftxt):
        descwrite(i)

    if os.path.exists(pi.fmp3):
        # plik jest
        pi.siz3 = os.stat(pi.fmp3).st_size
        if pi.siz3 == pi.size:
            log.debug("Skipping {}".format(pi.fmp3))
            continue
        else:
            log.info(
                "{} only {}<{} retrived - resuming".format(pi.fmp3,
                    pi.siz3, pi.size))
            try:
                # it takes some time for large files
                urllib._urlopener = PodcastURLopener()
                urllib._urlopener.addheader("Range", "bytes=%s-" % (pi.siz3))
                if args.verbose > 1 and not args.silent:
                    urllib.urlretrieve(pi.url, pi.tmp3, reporthook=reporthook)
                else:
                    urllib.urlretrieve(pi.url, pi.tmp3)
                urllib._urlopener = urllib.FancyURLopener()
                fsrc = open(pi.tmp3)
                fdst = open(pi.fmp3, "a")
                shutil.copyfileobj(fsrc, fdst)
                fsrc.close()
                fdst.close()
                os.unlink(pi.tmp3)

            except urllib.ContentTooShortError:
                log.warning("failed to retrieve {} ".format(pi.url))
                if os.path.exists(pi.tmp3):
                    log.debug("removing {}".format(pi.tmp3))
                    os.unlink(pi.tmp3)
                continue

    else:
        log.info("Downloading {}".format(pi.fmp3))
        try:
            # it takes some time for large files
            if args.verbose:
                urllib.urlretrieve(pi.url, pi.fmp3, reporthook=reporthook)
            else:
                urllib.urlretrieve(pi.url, pi.fmp3)

        except urllib.ContentTooShortError:
            log.warning("failed to retrieve {}".format(pi.url))
            if os.path.exists(pi.fmp3):
                log.debug("removing {}".format(pi.fmp3))
                os.unlink(pi.fmp3)
            continue

        log.debug("stored as {}".format(pi.fmp3))
