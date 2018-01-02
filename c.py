from random import choice

from bs4 import BeautifulSoup
import Podcast

p = Podcast.testPodcast()
pi = next(p)


def main():
    c = choice()


class Person:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.make_greeting()

    def make_greeting(self):
        f = "Hello {}"
        return f.format(self.name)


if __name__ == '__main__':
    main()
