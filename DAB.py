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
    def init_filenaming_scheme(self):
        """Podcast File Naming Scheme.

        Transforms current podcast file names according to rules defined
        below. It overrides a generic method from PodcastItem class.
        """

        p = re.compile(r'(.*?)\s+(January|February|March|April|May|June|'
                       r'July|August|September|October|November|December).*')
        self.myname = p.sub(r'\1', self.name)
        ff = {'date': self.date,
              'name': self.myname.replace(' ', ''),
              'ext': self.remote_file_suffix}
        self.file = '{date:%Y%m%d}_{name}'.format(**ff)
        self.file_data = '{date:%Y%m%d}_{name}{ext}'.format(**ff)
        self.file_temp = self.file_data + '.part'
        self.file_txt = self.file + '.txt'

