from unittest import TestCase


class TestPodcastItem(TestCase):
    def test_initFileNamingScheme(self):
        from Podcast import PodcastItem
        from bs4 import BeautifulSoup, Tag
        # Podcast item not properly initialized,
        # looks like Tag has wrong __repr__

        soup = BeautifulSoup('''<item><title>DAB December 25- 2015</title>
<description>Zech  8:1-23,  Rev  16:1-21,   Ps 144:1-15,   Pr 30:29-31&lt;img src="http://feeds.feedburner.com/~r/dailyaudiobible/~4/uksklMI3kfw" height="1" width="1" alt=""/&gt;</description>
<link/>http://feedproxy.google.com/~r/dailyaudiobible/~3/uksklMI3kfw/
            <author>brian@dailyaudiobible.com (Brian Hardin)</author>
<category domain="www.dailyaudiobible.com">Religion &amp; Spirituality Christianity Spoken Word Performing Arts Religion Spirituality</category>
<guid ispermalink="false">25690E2A-F464-445E-A4CE-91C885480F63-10990-00009828E03F474A-FFA</guid>
<pubdate>Thu, 24 Dec 2015 19:00:00 -0600</pubdate>
<media:content filesize="17" type="audio/mpeg" url="http://feedproxy.google.com/~r/dailyaudiobible/~5/QlTg-2hhxVs/December25-2015.m4a"></media:content><itunes:explicit>no</itunes:explicit><itunes:subtitle>1 Year Daily Audio Bible</itunes:subtitle><itunes:author>Brian Hardin</itunes:author><itunes:summary>One year. Every day. 365 days through the Bible in community with tens of thousands of others around the globe on the same journey. Broadcast daily from the rolling hills of Tennessee, Nashville based record producer and author Brian Hardin is your guide on the adventure of a lifetime. Also visit our sister programs: Daily Audio Proverb, Daily Audio Psalm, Daily Audio Bible Kids, Daily Audio Bible En Espanol, Daily Audio Bible Japanese and Daily Audio Bible Arabic. Visit us on the web at www.dailyaudiobible.com</itunes:summary><itunes:keywords>Daily,Audio,Bible,Scripture,Community,Christianity,Global,WindFarm,Prayer,Jesus,God,Holy,Spirit,Christian,Spirituality</itunes:keywords><feedburner:origlink>http://www.dailyaudiobible.com</feedburner:origlink><enclosure length="17" type="audio/mpeg" url="http://feedproxy.google.com/~r/dailyaudiobible/~5/QlTg-2hhxVs/December25-2015.m4a"></enclosure><feedburner:origenclosurelink>http://podcast.dailyaudiobible.com/mp3/December25-2015.m4a</feedburner:origenclosurelink>
</item>''', 'lxml')

        item = soup.find('item')
        pi = PodcastItem(item)
        self.assertIsNotNone(pi.myname)
        self.assertIsNotNone(pi.file)
        self.assertIsNotNone(pi.file_data)
        self.assertIsNotNone(pi.file_temp)
        self.assertIsNotNone(pi.file_txt)
