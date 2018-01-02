#!/usr/bin/python3

import unittest
from Podcast import Podcast, PodcastItem

PODCAST_URL = 'http://feeds.feedburner.com/dailyaudiobible/'


class TestPodcast(unittest.TestCase):

    def test_podcast(self):
        p = Podcast(PODCAST_URL)

    def test_podcastitems(self):
        for pi in Podcast(PODCAST_URL):
            print("myname:%s\n\tdate:%s\n\tfilename:%s\n\tbase:%s sufx:%s" % \
                (pi.myname, pi.date, pi.file_data, pi.file_base, pi.file_suffix))


if __name__ == '__main__':
    unittest.main()
