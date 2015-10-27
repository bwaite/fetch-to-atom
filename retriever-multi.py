#! /usr/bin/env python3

import pycurl
import yaml
import argparse
import io
from extractor import ExtractorFactory

# We should ignore SIGPIPE when using pycurl.NOSIGNAL - see
# the libcurl tutorial for more info.
try:
    import signal
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
except ImportError:
    pass


parser = argparse.ArgumentParser()
parser.add_argument('urls_file', type=str,
                    help='the file with the urls to be fetched')
parser.add_argument('--num-conn', type=int, default=10,
                    help='number of connections to use (default: 10)')

args = parser.parse_args()

conf = yaml.load(open('conf.yml'))

num_conn = args.num_conn
urls_file = args.urls_file

queue = []
with open(urls_file) as f:
    for url in f.readlines():
        url = url.strip()
        if not url or url[0] == "#":
            continue
        queue.append(url)

# Check args
assert queue, "no URLs given"
num_urls = len(queue)
num_conn = min(num_conn, num_urls)
assert 1 <= num_conn <= 10000, "invalid number of concurrent connections"
print("----- Getting", num_urls, "URLs using", num_conn, "connections -----")


# Pre-allocate a list of curl objects
m = pycurl.CurlMulti()
m.handles = []
for i in range(num_conn):
    c = pycurl.Curl()
    c.fp = None
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.MAXREDIRS, 5)
    c.setopt(pycurl.CONNECTTIMEOUT, 30)
    c.setopt(pycurl.TIMEOUT, 300)
    c.setopt(pycurl.NOSIGNAL, 1)

    # if conf['curl_http_headers']:
    #     c.setopt(pycurl.HTTPHEADER, conf['curl_http_headers'])

    if conf['curl_user_agent']:
        c.setopt(pycurl.USERAGENT, conf['curl_user_agent'])

    m.handles.append(c)


# Main loop
freelist = m.handles[:]
num_processed = 0
while num_processed < num_urls:
    # If there is an url to process and a free curl object, add to multi stack
    while queue and freelist:
        url = queue.pop(0)
        c = freelist.pop()
        c.fp = io.BytesIO()
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.WRITEDATA, c.fp)
        m.add_handle(c)
        c.url = url

    # Run the internal curl state machine for the multi stack
    while True:
        ret, num_handles = m.perform()
        if ret != pycurl.E_CALL_MULTI_PERFORM:
            break

    # Check for curl objects which have terminated, and add them to the freelist
    while True:
        num_q, ok_list, err_list = m.info_read()

        for c in ok_list:
            s = str(c.fp.getvalue())
            c.fp.close()
            c.fp = None
            m.remove_handle(c)
            print("Success:", c.url, c.getinfo(pycurl.EFFECTIVE_URL))

            ext = ExtractorFactory(c.url, s)
            if ext:
                articles = ext.extract()
                ext.insert_in_db(articles)
            else:
                print("No Extractor Found for URL")

            freelist.append(c)

        for c, errno, errmsg in err_list:
            c.fp.close()
            c.fp = None
            m.remove_handle(c)
            print("Failed: ", c.url, errno, errmsg)
            freelist.append(c)
        num_processed = num_processed + len(ok_list) + len(err_list)
        if num_q == 0:
            break

    # Currently no more I/O is pending, could do something in the meantime
    # (display a progress bar, etc.).
    # We just call select() to sleep until some more data is available.
    m.select(1.0)


# Cleanup
for c in m.handles:
    if c.fp is not None:
        c.fp.close()
        c.fp = None
    c.close()
m.close()
