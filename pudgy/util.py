import hashlib
import time
import os

import flask

def inheritors(klass):
    subclasses = set()
    work = [klass]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                work.append(child)
    return subclasses

# from https://stackoverflow.com/questions/16463582/memoize-to-disk-python-persistent-memoization
# https://stackoverflow.com/posts/47385932/revisions
from diskcache import Cache
cache_dir = "./cache/"
def shelve_it(table_name):
    cache_file = os.path.join(cache_dir, table_name)
    d = Cache(cache_file)

    def decorator(func):
        def new_func(*args, **kwargs):
            cache_key = "\r".join([str(arg) for arg in args])

            if cache_key in d:
                return d[cache_key]


            ret = func(*args, **kwargs)
            d[cache_key] = ret

            return ret

        return new_func

    return decorator

def memoize(func):
    cache = {}
    def new_func(*args, **kwargs):
        cache_key = "\r".join([str(arg) for arg in args])
        if kwargs:
            cache_key += "\r".join(["%s:%s" % (k,v) for k,v in kwargs.iteritems()])

        if cache_key in cache:
            return cache[cache_key]

        ret = func(*args, **kwargs)
        cache[cache_key] = ret
        return ret

    return new_func

def gethash(v):
    m = hashlib.md5()
    h = str(hash(v)).encode("utf-8")

    m.update(h)

    return m.hexdigest()

def getrandhash(v):
    m = hashlib.md5()
    t = str("%s" % time.time()).encode("utf-8")
    h = str(hash(v)).encode("utf-8")

    m.update(t)
    m.update(h)

    return m.hexdigest()

def handle_request_to(endpoint, **values):
    url = flask.url_for(endpoint, **values)
    req = flask.Request.from_values(path=url)
    ctx = flask.current_app.test_request_context(path=url)

    with ctx:
        res = flask.current_app.dispatch_request()
    return res

def dated_url_for(endpoint, **values):
    app = flask.current_app
    # we know prelude always returns a string, so
    # we use python string hashing
    if endpoint == 'components.get_prelude':
        res = handle_request_to(endpoint, **values)
        hsh = hash(res)

        values['q'] = "%x" % (hsh)

    if endpoint == 'components.get_big_css':
        res = handle_request_to(endpoint, **values)
        hsh = hash(res)

        values['q'] = "%x" % (hsh)

    # if the endpoint is a filename, we use timestamp hashing
    # (but we should really use content hashing, i guess)
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)

    return flask.url_for(endpoint, **values)

