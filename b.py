import os
import urllib2
import urllib
import httplib
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
import email.utils as eut
#from datetime import datetime
import datetime
import codecs
from urlparse import urlparse
import shutil

current_page = open('cache-soup.html')
soup = BeautifulSoup(current_page)

