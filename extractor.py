#! /usr/bin/env python3

import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import db


class AtomArticle(object):
    def __init__(self, url, title):

        self.url = url
        self.title = title,
        # content=row.content,
        # content_type="html",
        # author=row.title,
        # url=row.title,
        # updated=dt


def ExtractorFactory(url, contents):

    u = urlparse(url)

    if u.netloc == "imgur.com":
        return ImgurExtractor(url, contents)


class Extractor(object):

    def __init__(self, url, contents):
        self.url = url
        self.time = datetime.datetime.utcnow()
        self.contents = contents
        self.soup = BeautifulSoup(contents, "lxml")

    def insert_in_db(self, articles):
        rows = []

        for article in articles:
            art = {'title': article.title,
                   'author': None,
                   'url': article.url,
                   'updated': self.time}

            rows.append(art)

        result = db.conn.execute(db.articles.insert(), rows)

    def extract(self):
        pass

class ImgurExtractor(Extractor):

    def __init__(self, url, contents):
        super().__init__(url, contents)

    def extract(self):
        # Do stuff with self.soup

        images = self.soup.select(".post")

        articles = []
        for i in images:
            title = i.select(".hover > p")[0].text
            url = i.select("a > img")[0].attrs['src'].replace("//", "")
            url = "https://" + url
            articles.append(AtomArticle(url, title))

        return articles
