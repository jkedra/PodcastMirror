# -*- coding: utf-8 -*-
# vim:ts=4:expandtab
# (c) Jerzy Kędra 2015-2016
# Python 3.5
"""
Created on Tue Feb  3 19:04:35 2015
@author: acer
"""

import re
from Podcast import Podcast, PodcastItem

class DABItem(PodcastItem):
    def initFileNamingScheme(self):
        """Podcast File naming scheme
        Transform current podcast file names or setup a brand new file name
        for ongoing podcast files.
        It is responsible for initialization of following fields:
        1) myname (customized item name - where possible shall be
                                          common for all items)
        2) file (local file base for txt and audio)
        """

        p = re.compile(r'(.*?)\s+(January|February|March|April|May|June|July|August|September|October|November|December).*')
        self.myname = p.sub(r'\1', self.name)
        ff = { 'date' : self.date,
               'name' : self.myname.replace(' ', ''),
               'ext'  : self.remote_file_suffix }
        self.file = '{date:%Y%m%d}_{name}'.format(**ff)
        self.file_data = '{date:%Y%m%d}_{name}{ext}'.format(**ff)
        self.file_temp = self.file_data + '.part'
        self.file_txt = self.file + '.txt'

# TODO: below makes no sense - better deliver item class as a parameter
class DAB(Podcast):
    """Use DABItem instead of PodcastItem
    """

    def __next__(self):
        if self.index == 0:
            raise StopIteration
        self.index = self.index - 1
        return DABItem(self.podcasts[self.index])
