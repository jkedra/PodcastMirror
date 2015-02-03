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

#
import argparse
import logging
import ConfigParser
from Podcast import Podcast
import datetime
#
#import mp3

def initLog(log, args):
    """Initialize logging system"""
    log_levels = {None : logging.WARN,
                  1 : logging.INFO,
                  2 : logging.DEBUG}

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


# MAIN PROGRAM STARTS HERE
# KeyboardInterrupt
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
        log.debug("{} {} too old".format(pi.name, pi.date))
        continue

    # czy plik w ogóle da się ściągnąć, iterujemy od początku jak nie
    try:
        pi.getsize()
    except (IOError, TypeError) as e:
        print "IOError, TypeError %s" % e
        continue
   
        
    verbose = args.verbose > 1 and not args.silent
    pi.download_description()
    pi.download(verbose)