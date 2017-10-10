#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim:ts=4:expandtab
# (c) Jerzy Kędra 2013-2016
# Python 3.5
""" Mirror.py : Mirror a podcast to local resource.

    This script is intended to be run daily from cron,
    and copy incoming podcasts into a local directory.
    Primarily designed to mirror Daily Audio Bible podcasts,
    after I have got caught with missing podcasts with end of
    the year, when Brian Hardin (the podcast's author) removed the old
    podcasts and started a new yearly cycle.
    Default config: mirror.cfg
    Config properties:

    TODO: limit max nr of podcasts downloaded in one pass.
"""

import os
import sys

#
import argparse
import logging
import configparser
from DAB import DABItem
from Podcast import Podcast
import datetime
#
# import mp3


def initLog(log, args):
    """Initialize logging system

    :params log: logger object
    :params args: argsparse.parse_args()
    """
    log_levels = {None: logging.WARN,
                  1: logging.INFO,
                  2: logging.DEBUG}

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
    """
    https://docs.python.org/3/howto/argparse.html
    https://docs.python.org/3/library/argparse.html#module-argparse

    Returns argparse.Namespace object.
    """
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

config = configparser.ConfigParser()
cf = config.read(['mirror.cfg', os.path.expanduser('~/.mirror.cfg')])
if len(cf) == 0:
    print("config file not found")
    sys.exit(-1)
else:
    log.debug("config file %s" % str(cf))

baseurl = config.get("RSS", "baseurl")
target_dir = config.get("Mirror", "data") or args.target

if not os.path.isdir(target_dir):
    os.makedirs(target_dir)
log.debug("changing dir to {}".format(target_dir))
os.chdir(target_dir)

for pi in Podcast(baseurl, DABItem):
    podcast_age = datetime.datetime.now() - pi.date
    if podcast_age > datetime.timedelta(days=args.days):
        log.debug("{} {} too old".format(pi.name, pi.date))
        continue

    # can you ever download the file, reiterate if not
    try:
        pi.getsize()
    except (IOError, TypeError) as e:
        print(("IOError, TypeError %s" % e))
        continue

    verbose = args.verbose and args.verbose > 1 and not args.silent
    pi.download_description()
    pi.download(verbose)
