import unittest
from unittest import TestCase


class TestPodcastItem(TestCase):
    def test_initFileNamingScheme(self):
        from Podcast import PodcastItem
        from bs4 import BeautifulSoup
        # Podcast item not properly initialized,
        # looks like Tag has wrong __repr__

        with open('html/item.html') as f:
            soup = BeautifulSoup(f, 'lxml')
            item = soup.find('item')
        pi = PodcastItem(item)
        self.assertIsNotNone(pi.myname)
        self.assertIsNotNone(pi.file)
        self.assertIsNotNone(pi.file_data)
        self.assertIsNotNone(pi.file_temp)
        self.assertIsNotNone(pi.file_txt)

    @unittest.expectedFailure
    def test_download(self):
        """

        TODO:
        :return:
        """
        from Podcast import PodcastItem
        from bs4 import BeautifulSoup, Tag
        self.fail()
