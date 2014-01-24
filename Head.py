#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:ts=4:expandtab
import httplib
from urlparse import urlparse

def getsize(url):	# returns size of the http object, follows redir
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
		print "UNKNOWN PROBLEM"
		print res.reason, ": ", res.getheader('location')
		print res.getheaders()
		return 0


print getsize("http://feedproxy.google.com/~r/zdzis/~5/Gsh06j8mle4/mpp-339.mp3")

