# -*- coding: utf-8 -*-
# vim:ts=4:expandtab
# (c) Jerzy Kędra 2015-2016
# Python 2.7
"""
Created on Tue Feb  3 12:19:07 2015
@author: Jerzy Kędra
"""
# TODO: https://www.crummy.com/software/BeautifulSoup/bs4/doc/#method-names
import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error
import http.client
import os
import shutil
from bs4 import BeautifulSoup, Tag
import codecs
from urllib.parse import urlparse
import email.utils as eut
import datetime
import logging


class PodcastURLopener(urllib.request.FancyURLopener):
    """This is just FancyURLopener with an overriden sub-class for error 206.

       The error means a partial file is being sent,
       which is ok in this case - so silently ignore the error.
    """
    def http_error_206(self, url, fp, errcode, errmsg, headers, data=None):
        pass


def appendThenRemove(src_name, dst_name):
    """Append to the end of destination and unlink the source."""

    fsrc = open(src_name)
    fdst = open(dst_name, "a")
    shutil.copyfileobj(fsrc, fdst)
    fsrc.close()
    fdst.close()
    os.unlink(src_name)


def humanBytes(bytes):
        if bytes < 1024*1024:
            return '%dkB' % (bytes/1024)
        elif bytes > 1024*1024:
            return '%dMB' % (bytes/1024/1024)


class PodcastItem:
    """ Parse and store BeautifulSoup.Tag information.

    Fields:
        url   - Item URL to download.
        name  - Original item name.
        date  - Item publication date.
        descr - Item description.

    You might need to override initFileNamingScheme method.
    """

    def __init__(self, item):
        if type(item) is not Tag:
            return
        self.item = item
        self.log = logging.getLogger("__main__")
        self.name = item.title.string.strip()
        # self.url = item.find('media:content').find(
        #  'feedburner:origenclosurelink').string.strip();
        self.url = item.find('media:content')['url']
        self.date = datetime.datetime(*eut.parsedate(item.pubdate.string)[:6])
        self.descr = item.description.string.strip()

        self.remote_file_name = os.path.basename(self.url)
        (self.remote_file_base,
         self.remote_file_suffix) = os.path.splitext(self.remote_file_name)


        self.size = 0
        self._sizesofar = 0

        # initialized by initFileNamingScheme
        self.myname = None
        self.file = None
        self.file_data = None
        self.file_temp = None
        self.file_txt = None
        self.initFileNamingScheme()

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.item)

    def initFileNamingScheme(self):
        """Podcast File Naming Scheme

        Transform current podcast file names or setup a brand new file name
        for ongoing podcast files. This method should be overridden later
        in a subclass. When overriding this method you are responsible
        for initialization of all "file" fields mentioned below.

        It is responsible for initialization of following fields:
        :myname: customized item name - shall be common for all items)
        :file:   local file basename (no suffix) for txt and audio
        :file_data: filename for storing media
        :file_temp: filename for storing temporary media file
        :file_txt: filename for storing text description for matching media
        """
        self.myname = self.name
        self.file = self.remote_file_base
        self.file_data = self.remote_file_name
        self.file_temp = self.file_data + '.part'
        self.file_txt = self.file + '.txt'

    def reporthook(self, blocks_read, block_size, total_size):
        """Print progress. Used by urllib.urlretrieve."""
        total_size = self.size
        if not blocks_read:
            return
        if total_size < 0:
            # Unknown size
            print(' Read %d blocks' % blocks_read)
        else:
            amount_read = blocks_read * block_size + self._sizesofar
            print(' Read %s %d%%       \r' %
                  (humanBytes(amount_read), 100*amount_read/total_size),
                  end=' ')
        return

    def download_description(self):
        """Dump the podcast item description into a file."""
        if os.path.exists(self.file_txt):
            return
        bf = BeautifulSoup(self.descr, 'lxml').contents[0].get_text()
        descr = "{}\n{}\n".format(self.name, bf)
        f = codecs.open(self.file_txt, encoding='utf-8', mode='w')
        f.write(descr)
        f.close()

    def getsize(self, url=None):
        """Return Content-Length value for given URL. Follow redirs.

        :param url: http url
        :returns: Size of object in bytes.
        """
        o = urlparse(url or self.url)
        conn = http.client.HTTPConnection(o.netloc)
        conn.request("HEAD", o.path)
        res = conn.getresponse()

        # https://docs.python.org/2/library/httplib.html
        statuses = (http.client.MOVED_PERMANENTLY, http.client.FOUND)
        if res.status in statuses:
            # print res.reason, ": ", res.getheader('location')
            return self.getsize(res.getheader('location'))
        elif res.status == http.client.OK:
            # inne interesujace tagi: etag
            self.size = int(res.getheader('content-length'))
            return self.size
        else:
            self.log.warn("getsize() UNKNOWN PROBLEM")
            print("{}: {} ".format(res.reason, res.getheader('location')))
            print(res.getheaders())
            raise IOError

    def contentInvalidCleanup(self, url, path):
        """Cleanup after the exception.

        Can be due to content to short or invalid MP3."""
        self.log.warning("failed to retrieve %s " % url)
        if os.path.exists(path):
            self.log.debug("removing %s" % path)
            os.unlink(path)

    def download(self, verbose=False):
        """Download Podcast Item"""

        file_data = self.file_data
        size = self.size
        sizesofar = self._sizesofar
        url = self.url
        file_temp = self.file_temp
        l = self.log
        r = urllib.request

        if verbose:
            report_type = self.reporthook
        else:
            report_type = None

        if os.path.exists(file_data):
            sizesofar = os.stat(file_data).st_size
            file_complete = (sizesofar == size)
            if file_complete:
                l.debug("Skipping {}".format(file_data))
                return
            else:
                l.info("%s partially retrieved - resuming" % file_data)
                l.debug("only {}<{} retrived".format(sizesofar, size))
                try:
                    r._urlopener = PodcastURLopener()
                    r._urlopener.addheader("Range", "bytes=%s-" % (sizesofar))
                    r.urlretrieve(url, file_temp, reporthook=report_type)
                    r._urlopener = urllib.request.FancyURLopener()
                    appendThenRemove(file_temp, file_data)
                except urllib.error.ContentTooShortError:
                    self.contentInvalidCleanup(url, file_temp)
                    return
        # first time download
        else:
            l.info("Downloading {}".format(file_data))
            try:
                r.urlretrieve(self.url, file_data, reporthook=report_type)
            except urllib.error.ContentTooShortError:
                self.contentInvalidCleanup(self.url, file_data)
                return

        l.debug("stored as {}".format(file_data))


class Podcast:
    """Represents Podcast(url, days). Allows iterating over podcasts.

    url - source of the podcast
    days - how far in the past look behind
    soup - Beautiful Soup of the Podcast

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
        self.index = 0
        self.url = url
        try:
            self.soup = BeautifulSoup(urllib.request.urlopen(url), 'lxml')
            self.podcasts = self.soup.findAll('item')
            self.index = len(self.podcasts)
        except urllib.error.URLError as e:
            print("%s" % e.value)

    def __iter__(self):
        return self

    def __next__(self):
        if self.index == 0:
            raise StopIteration
        self.index -= 1
        return PodcastItem(self.podcasts[self.index])

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.url)


def testPodcast():
    return Podcast('http://feeds.feedburner.com/dailyaudiobible/')


def testPodcastItem():
    p = testPodcast()
    return next(p)


def testPodcastItems():
    for pi in testPodcast():
        print("myname:%s\n\tdate:%s\n\tfilename:%s\n\tbase:%s sufx:%s" % \
            (pi.myname, pi.date, pi.file_data, pi.file_base, pi.file_suffix))

