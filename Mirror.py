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
#
import mp3


class PodcastURLopener(urllib.FancyURLopener):
    """Create sub-class in order to overide error 206.
    
       The error means a partial file is being sent,
       which is ok in this case. Do nothing with this error.
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
        amount_read = blocks_read * block_size + pi.sizesofar
        print ' Read ',
        if amount_read < 1024*1024:
            print '%dkB ' % (amount_read/1024),
        elif amount_read > 1024*1024:
            print '%dMB ' % (amount_read/1024/1024),

        print '%d%%    \r' % (100*amount_read/total_size),
    return


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

def appendThenRemove(src_name, dst_name):
    """Append to the end of destination and unlink the source"""
    fsrc = open(src_name)
    fdst = open(dst_name, "a")
    shutil.copyfileobj(fsrc, fdst)
    fsrc.close()
    fdst.close()
    os.unlink(src_name);
    
def contentInvalidCleanup(url, path):
    """Cleanup after the exception
       Can be due to content to short or invalid MP3."""
    log.warning("failed to retrieve %s " % url)
    if os.path.exists(path):
        log.debug("removing %s" % path)
        os.unlink(path)
                
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
    """Parse and store BeautifulSoup.Tag information."""
    
    def __init__(self, item):
        if type(item) is not Tag:
            return
        self.name = item.title.string.strip()
        self.date = datetime.datetime(*eut.parsedate(item.pubdate.string)[:6])
        self.description = item.description.string.strip()
        self.file_mp3 = self.name + '.mp3'
        self.file_temp = self.name + '.mp3.part'
        self.file_txt = self.name + '.txt'
        self.url = item.find('media:content')['url']
        self.file_name = os.path.basename(self.url)
        self.sizesofar = 0
        self.size = 0

    def dump_description(self):
        """Dump the podcast item description into a file"""
        
        f = codecs.open(self.file_txt, encoding='utf-8', mode='w')
        f.write(self.name)
        f.write("\n\n")
        # enclosing in try-exception because of following exceptin
        # TypeError: coercing to Unicode: need string or buffer, Tag found
        try:
            # This is to decode &lt/&gt before writing it to the file
            # BeautifulStoneSoup(items[1].description.string,
            #       convertEntities=BeautifulStoneSoup.HTML_ENTITIES).contents[0]
            f.write(BeautifulStoneSoup(self.description.string,
                                convertEntities=
                                BeautifulStoneSoup.HTML_ENTITIES).contents[0])
        # AttributeError: 'unicode' object has no attribute 'string'
        except (TypeError, AttributeError):
            f.write(BeautifulStoneSoup(self.description,
                                convertEntities=
                                BeautifulStoneSoup.HTML_ENTITIES).contents[0])
        f.close()
            
    def getsize(self, url=None):
        """Return Content-Length value for given URL. Follow redirs."""
                    
        o = urlparse(url or self.url)
        conn = httplib.HTTPConnection(o.netloc)
        conn.request("HEAD", o.path)
        res = conn.getresponse()
    
        # https://docs.python.org/2/library/httplib.html
        statuses = (httplib.MOVED_PERMANENTLY, httplib.FOUND)
        if res.status in statuses:
            # print res.reason, ": ", res.getheader('location')
            return self.getsize(res.getheader('location'))
        elif res.status == httplib.OK:
            # inne interesujace tagi: etag
            self.size = int(res.getheader('content-length'))
            return self.size
        else:
            log.warn("getsize() UNKNOWN PROBLEM")
            print "{}: {} ".format(res.reason, res.getheader('location'))
            print res.getheaders()
            raise IOError


class Podcast:
    """
    Represents Podcast(url, days)
        Allows itearating over podcasts.
       
    url - defines the podcast
    days - how far in the past look behind
       
    channel
        title
        lastBuildDate
        image
            url
        item
            title
            description
            link
            pubdate
            
    """
    def __init__(self, url):
        self.soup = BeautifulSoup(urllib2.urlopen(url))
        self.podcasts = self.soup.findAll('item')
        self.index = len(self.podcasts)
        
    def __iter__(self):
        return self
        
    def next(self):
        if self.index == 0:
            raise StopIteration
        self.index = self.index - 1
        return PodcastItem(self.podcasts[self.index])


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

if not os.path.isdir(args.target):
    os.makedirs(args.target)
log.debug("changing dir to {}".format(args.target))
os.chdir(args.target)

    
for pi in Podcast(baseurl):

    podcast_age = datetime.datetime.now() - pi.date
    if podcast_age > datetime.timedelta(days=args.days):
        log.debug("{} too old".format(pi.name, pi.date))
        continue

    # czy plik w ogóle da się ściągnąć, iterujemy od początku jak nie
    try:
        pi.getsize()
    except (IOError, TypeError) as e:
        print "IOError, TypeError %s" % e
        continue
    
    if not os.path.exists(pi.file_txt): pi.dump_description()

    if args.verbose > 1 and not args.silent:
        report_type = reporthook
    else:
        report_type = None
    
    # exists or continuation
    if os.path.exists(pi.file_mp3):
        pi.sizesofar = os.stat(pi.file_mp3).st_size
        file_complete = (pi.sizesofar == pi.size)
        
        if file_complete:
            if mp3.isMp3Valid(pi.file_mp3):
                log.debug("Skipping {}".format(pi.file_mp3))
                continue
            else:
                log.debug("%s is not a valid mp3 file" % pi.file_mp3)
                contentInvalidCleanup(pi.url, pi.file_temp)
                continue
        else:
            log.info("%s partially retrieved - resuming" % pi.file_mp3)
            log.debug("only {}<{} retrived".format(pi.sizesofar, pi.size))
            try:
                urllib._urlopener = PodcastURLopener()
                urllib._urlopener.addheader("Range", "bytes=%s-" % (pi.sizesofar))
                urllib.urlretrieve(pi.url, pi.file_temp, reporthook=report_type)
                
                urllib._urlopener = urllib.FancyURLopener()
                appendThenRemove(pi.file_temp, pi.file_mp3)
            except urllib.ContentTooShortError:
                contentInvalidCleanup(pi.url, pi.file_temp)
                continue
    # first time download
    else:
        log.info("Downloading {}".format(pi.file_mp3))
        try:
            urllib.urlretrieve(pi.url, pi.file_mp3, reporthook=report_type)
        except urllib.ContentTooShortError:
            contentInvalidCleanup(pi.url, pi.file_mp3)
            continue

        log.debug("stored as {}".format(pi.file_mp3))
