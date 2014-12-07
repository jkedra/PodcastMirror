#!/usr/bin/python
#-*- coding: utf-8 -*-
""" vim:ts=4:expandtab
    (c) Jerzy Kędra 2013-2014
    Python 2.7
    TODO(Jurek): nothing currently

"""
import os
import urllib2
import urllib
import httplib
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
#from datetime import datetime
import email.utils as eut
import datetime
#
import codecs
from urlparse import urlparse
import shutil
import argparse
import logging


class PodcastURLopener(urllib.FancyURLopener):
    """Create sub-class in order to overide error 206.  This error means a
       partial file is being sent, which is ok in this case.
       Do nothing with this error.
    """
    def http_error_206(self, url, fp, errcode, errmsg, headers, data=None):
        pass

def reporthook(blocks_read, block_size, total_size):
    """Progress printing, it is an argument to urlretrieve."""
    total_size = podsize

    if not blocks_read:
        return
    if total_size < 0:
        # Unknown size
        print ' Read %d blocks' % blocks_read
    else:
        amount_read = blocks_read * block_size + podsiz3
        print ' Read ',
        if amount_read < 1024*1024:
            print '%dkB ' % (amount_read/1024),
        elif amount_read > 1024*1024:
            print '%dMB ' % (amount_read/1024/1024),

        print '%d%%    \r' % (100*amount_read/total_size),
    return


# returns size of the http object, follows redirs
def getsize(url):
    """Returns Content-Length value for given URL. Follows redirs."""
    o = urlparse(url)
    conn = httplib.HTTPConnection(o.netloc)
    conn.request("HEAD", o.path)
    res = conn.getresponse()

    if res.status == 301 or res.status == 302:	# poprawic na kod opisowy
        # print res.reason, ": ", res.getheader('location')
        return getsize(res.getheader('location'))

    elif res.status == 200:
        # inne interesujace tagi: etag
        return res.getheader('content-length')
    else:
        log.warn("getsize() UNKNOWN PROBLEM")
        log.warn("{}: {} ".format(res.reason, res.getheader('location')))
        log.warn(res.getheaders())
        raise IOError

def descwrite(i):
    """Writes a description in a file for given podcast."""
    podnm = i.title.string
    f = codecs.open(podftxt, encoding='utf-8', mode='w')

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
    """Initializes logging system"""
    log_levels = { 0 : logging.WARN,
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

# MAIN PROGRAM STARTS HERE
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", action="count",
                    help="increases verbosity")
parser.add_argument("-d", "--days", type=int, default=30,
                    help="how far in the past go")
parser.add_argument("-t", "--target", default="DATA",
                    help="target data directory")
parser.add_argument("-l", "--logfile",
                    help="logging to file, log file path required")
parser.add_argument("-s", "--silent", action="store_true",
                    help="silent mode - suppress terminal output")
args = parser.parse_args()

log = logging.getLogger(__name__)
initLog(log, args)


#baseurl = 'http://feeds.feedburner.com/zdzis?format=xml/'
baseurl = 'http://feeds.feedburner.com/dailyaudiobible/'
current_page = urllib2.urlopen(baseurl)
soup = BeautifulSoup(current_page)

if not os.path.isdir(args.target):
    os.makedirs(args.target)
log.debug("changing dir to {}".format(args.target))
os.chdir(args.target)


for i in soup.findAll('item'):
    podname = i.title.string
    poddate = datetime.datetime(*eut.parsedate(i.pubdate.string)[:6])
    podfmp3 = podname + '.mp3'
    podtmp3 = podname + '.mp3.part'
    podftxt = podname + '.txt'
    podurl = i.find('media:content')['url']
    podsiz3 = 0
    posize = 0

    if datetime.datetime.now() - poddate > datetime.timedelta(days=args.days):
        log.debug("{} too old".format(podname, poddate))
        continue

    # sprawdźmy czy plik w ogóle da się ściągnąć
    # jak nie - iterujemy od początku
    try:
        podsize = int(getsize(podurl))
    except (IOError, TypeError) as e:
        continue

    # write description to description file
    if not os.path.exists(podftxt):
        descwrite(i)

    if os.path.exists(podfmp3):
        # plik jest
        podsiz3 = os.stat(podfmp3).st_size
        if podsiz3 == podsize:
            log.debug("Skipping {}".format(podfmp3))
            continue
        else:
            log.info(
                "{} only {}<{} retrived - resuming".format(podfmp3,
                    podsiz3, podsize))
            try:
                # it takes some time for large files
                urllib._urlopener = PodcastURLopener()
                urllib._urlopener.addheader("Range", "bytes=%s-" % (podsiz3))
                if args.verbose > 1 and not args.silent:
                    urllib.urlretrieve(podurl, podtmp3, reporthook=reporthook)
                else:
                    urllib.urlretrieve(podurl, podtmp3)
                urllib._urlopener = urllib.FancyURLopener()
                fsrc = open(podtmp3)
                fdst = open(podfmp3, "a")
                shutil.copyfileobj(fsrc, fdst)
                fsrc.close()
                fdst.close()
                os.unlink(podtmp3)

            except urllib.ContentTooShortError:
                log.warning("failed to retrieve {} ".format(podurl))
                if os.path.exists(podtmp3):
                    log.debug("removing {}".format(podtmp3))
                    os.unlink(podtmp3)
                continue

    else:
        log.info("Downloading {}".format(podfmp3))
        try:
            # it takes some time for large files
            if args.verbose:
                urllib.urlretrieve(podurl, podfmp3, reporthook=reporthook)
            else:
                urllib.urlretrieve(podurl, podfmp3)

        except urllib.ContentTooShortError:
            log.warning("failed to retrieve {}".format(podurl))
            if os.path.exists(podfmp3):
                log.debug("removing {}".format(podfmp3))
                os.unlink(podfmp3)
            continue

        log.debug("stored as {}".format(podfmp3))
