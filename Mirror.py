#!/usr/bin/python
#-*- coding: utf-8 -*-
""" vim:ts=4:expandtab
    (c) Jerzy Kędra 2013
    Python 2.7
    TODO:
        1.Check only last few podcasts by date
          Don't try to download older podcasts than date specified.
          For example - test last week only for regular podcast
          donwload.
            
        2.Non-verbose mode to be used from cron.
    
"""
import os
import urllib2
import urllib
import httplib
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
#from datetime import datetime
import codecs
from urlparse import urlparse
import shutil


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
        if amount_read < 1024*1024 :
            print '%dkB ' % (amount_read/1024),
        elif amount_read > 1024*1024 :
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
        # print res.getheader('content-length')
        return res.getheader('content-length')
    else:
        print "getsize() UNKNOWN PROBLEM"
        print res.reason, ": ", res.getheader('location')
        print res.getheaders()
        raise IOError

def descwrite(i):
    """Writes a description in a file for given podcast."""
    podname = i.title.string
    f = codecs.open(podftxt, encoding='utf-8', mode='w')
    
    f.write(podname)
    f.write("\n\n")
    # enclosing in try-exception because of this error
    # TypeError: coercing to Unicode: need string or buffer, Tag found
    try:
        # This is to decode &lt/&gt before writing it to the file
        # BeautifulStoneSoup(items[1].description.string, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).contents[0]
        f.write(BeautifulStoneSoup(i.description.string,
                                   convertEntities=
                                   BeautifulStoneSoup.HTML_ENTITIES).contents[0])
    except TypeError:                     
        f.write(i.description.string)
        
    f.close


""" MAIN PROGRAM STARTS HERE
"""
#baseurl = 'http://feeds.feedburner.com/zdzis?format=xml/'
baseurl = 'http://feeds.feedburner.com/dailyaudiobible/'
current_page = urllib2.urlopen(baseurl)

#current_page = open('cache.html')
soup = BeautifulSoup(current_page)

# SAVING THE SOUP IN A FILE
fs = open('cache-soup.html', 'w')
fs.write(soup.prettify())
# exit()

"""
c = soup.find('div', {'id':'story'})
contpage = c.find('div', {'class':'articlePaged_Next'}).a['href']
soup.find('div', {'id':'story'})
if len(contpage) > 0 :
       current_page = urllib2.urlopen(baseurl+contpage)
    soupadd = BeautifulSoup(current_page).find('div', {'id':'story'})

items = soup.findAll('item')
print items[1].find('media:content')['url'], "\n\n\n",
    items[1].title.string, "\n\n\n", items[1].description.string
"""

os.chdir('DATA')
for i in soup.findAll('item'):
    podname = i.title.string
    podfmp3 = podname + '.mp3'
    podtmp3 = podname + '.mp3.part'
    podftxt = podname + '.txt'
    podurl  = i.find('media:content')['url']
    podsiz3 = 0
    posize  = 0
    
    
    # sprawdźmy czy plik w ogóle da się ściągnąć
    # jak nie - iterujemy od początku
    try:
        podsize = int(getsize(podurl))
    except (IOError, TypeError) as e:
        continue

    # write description to description file
    if not os.path.exists(podftxt) :
        descwrite(i)
    
    if os.path.exists(podfmp3) :
        # plik jest
        podsiz3 = os.stat(podfmp3).st_size   
        if podsiz3 == podsize :
            print "Skipping ", podfmp3
            continue
        else:
            print "{} only {}<{} retrived - resuming".format(podfmp3,
                    podsiz3, podsize)

            try:
                # it takes some time for large files
                urllib._urlopener = PodcastURLopener()
                urllib._urlopener.addheader("Range","bytes=%s-" % (podsiz3))
                urllib.urlretrieve(podurl, podtmp3, reporthook=reporthook)
                urllib._urlopener = urllib.FancyURLopener()
                fsrc = open(podtmp3)
                fdst = open(podfmp3, "a")
                shutil.copyfileobj(fsrc, fdst)
                fsrc.close()
                fdst.close()
                os.unlink(podtmp3)
            
            except urllib.ContentTooShortError:
                print "\tfailed to retrieve ", podurl
                if os.path.exists(podtmp3) :
                    print "\tremoving ", podtmp3
                    os.unlink(podtmp3)
                continue
    
    else :
        print "Downloading ", podfmp3    
        try:
            # it takes some time for large files
            urllib.urlretrieve(podurl, podfmp3, reporthook=reporthook)
        except urllib.ContentTooShortError:
            print "\tfailed to retrieve ", podurl
            if os.path.exists(podfmp3) :
                print "\tremoving ", podfmp3
                os.unlink(podfmp3)
            continue

        print "stored as ", podfmp3
 


