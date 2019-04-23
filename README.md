This is a project to mirror podcasts.
Primarily designed to mirror [Daily Audio Bible](https://dailyaudiobible.com/)
podcasts, after I have got caught with missing podcasts at end of
the year, when the podcast's author - Brian Hardin removed the old
podcasts and started a new yearly cycle.

This script is intended to be run daily from cron,
and copies incoming podcasts into a local directory.

Default config: mirror.cfg
Config properties:

Dependencies:

    apt-get install python-pip
    pip install bs4 lxml

# How to use?

    ./Mirror.py
    
# Quick Review

Useful for quickly reviewing all files.

    mplayer -ss 1 -endpos 11 *.m4a

