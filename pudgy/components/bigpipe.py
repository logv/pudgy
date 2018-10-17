from .components import *
from .basic import JSComponent

import flask
import time
import struct
import zlib

# https://stackoverflow.com/questions/44185486/generate-and-stream-compressed-file-with-flask
def streaming_compress(generator):
    # Yield a gzip file header first.
    yield (
        '\037\213\010\000' + # Gzip file, deflate, no filename
        struct.pack('<L', long(time.time())) +  # compression start time
        '\002\377'  # maximum compression, no OS specified
    )

    # bookkeeping: the compression state, running CRC and total length
    compressor = zlib.compressobj(
        9, zlib.DEFLATED, -zlib.MAX_WBITS, zlib.DEF_MEM_LEVEL, 0)
    crc = zlib.crc32("")
    length = 0

    for data in generator:
        chunk = compressor.compress(data)
        if chunk:
            yield chunk
        else:
            # note: do not use Z_FULL_FLUSH, it resets the compressor
            yield compressor.flush(zlib.Z_SYNC_FLUSH)

        crc = zlib.crc32(data, crc) & 0xffffffff
        length += len(data)

    yield compressor.flush()
    yield struct.pack("<2L", crc, length & 0xffffffff)


# This is the main loop for the preparer. It does a sleep spin
def sleep_spin(preparer, pagelets):
    start = time.time()
    pagelets = set(pagelets)
    while True:
        time.sleep(0.01)
        preparer.finish_tasks()

        remove = []
        for p in pagelets:
            if p.__finished__ and not p.__injected__:
                p.__injected__ = True
                remove.append(p)
                yield inject_pagelet(p)

        for p in remove:
            pagelets.remove(p)

        if preparer.done or not preparer.preparing:
            break

def inject_pagelet(pagelet):
    html = pagelet.render()
    t = "\n<div id='pagelet_%s'><!-- %s --></div>\n" % (pagelet.__html_id__(), flask.escape(html))
    i = "\n<script>$P._inject_pagelet('%s')</script>\n" % pagelet.__html_id__()
    return "\n".join([t, i])


class Pipeline(Component):
    def pipeline(self):

        flask.request.pudgy.pipelined = True



        stream =  flask.stream_with_context(self.run())
        accept_encoding = flask.request.headers.get('Accept-Encoding', '')
        if 'gzip' not in accept_encoding.lower():
            return flask.Response(stream)


        response = flask.Response(streaming_compress(stream))
        response.headers['Content-Encoding'] = 'gzip'

        return response

    def run(self):
        import preparable
        from ..blueprint import marshal_components

        kwargs = self.context.toDict()
        r = self.render()

        yield r
        yield marshal_components(prelude=True)

        preparer = preparable.Preparer()
        pagelets = []
        for p in flask.request.pudgy.pagelets:
            if not p.__async__:
                continue

            p.__done__ = False
            preparer.add(p.__prepare_pagelet__, [])
            pagelets.append(p)


        preparer.startup()
        for p in sleep_spin(preparer, pagelets):
            yield p

        for p in flask.request.pudgy.pagelets:
            if not p.__async__:
                continue

            flask.request.pudgy.components.add(p)

            if not p.__injected__:
                yield inject_pagelet(p)

        yield marshal_components(prelude=False)



class Pagelet(JSComponent):
    def __init__(self, *args, **kwargs):
        self.__finished__ = False
        self.__async__ = False
        super(Pagelet, self).__init__(*args, **kwargs)

        if flask.request:
            flask.request.pudgy.pagelets.add(self)

    def async(self):
        self.__async__ = True

    def render(self):
        if self.__async__ and not self.__finished__:
            t = """<div class='async_pagelet pagelet' id='pl_{{ id }}'> </div>"""
            r = pystache.render(t, { "id" : self.__html_id__() })
            return r
        else:
            return super(Pagelet, self).render()

    def __prepare_pagelet__(self):
        self.__injected__ = False
        import types
        r = self.__prepare__()

        if isinstance(r, types.GeneratorType):
            for p in r:
                yield p

            self.__finished__ = True
        else:
            self.__finished__ = True
            yield r


    def __activate_tag__(self):
        if self.__async__ and not self.__finished__:
            return ""

        return super(Pagelet, self).__activate_tag__()

    def __work__(self):
        pass

class NoJSPagelet(Pagelet):
    # has no JS file associated with it
    @classmethod
    def get_js(cls):
        return ""

mark_virtual(Pagelet, Pipeline, NoJSPagelet)
