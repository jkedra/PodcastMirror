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
        return res
    else:
        raise IOError

r1 = getsize('http://feedproxy.google.com/~r/dailyaudiobible/~5/APhtbDtnEXQ/December31-2014.m4a')
