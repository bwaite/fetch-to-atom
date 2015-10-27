#!/usr/bin/env python3

from flask import Flask, request
from werkzeug.contrib.atom import AtomFeed
from sqlalchemy.sql import select
import db

app = Flask(__name__)
# app.debug = True


@app.route("/recent.atom")
def hello():
    feed = AtomFeed('Recent Articles',
                    feed_url=request.url, url=request.url_root)

    s = select([db.articles]).order_by("updated")

    result = db.conn.execute(s)

    for row in result:
        feed.add(title=row.title,
                 content="",
                 content_type="html",
                 author=row.title,
                 url=row.url,
                 updated=row.updated)

    return feed.to_string()

if __name__ == "__main__":
    app.run()
