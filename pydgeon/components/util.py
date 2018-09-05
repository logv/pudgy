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

def memoize(func):
    cache = {}
    def new_func(*args, **kwargs):
        cache_key = "\r".join([str(arg) for arg in args])

        if cache_key in cache:
            return cache[cache_key]

        ret = func(*args, **kwargs)
        cache[cache_key] = ret
        return ret

    return new_func

