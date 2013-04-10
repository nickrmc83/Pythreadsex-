def default_return(d):
    '''
    default_return decorator
    Use this decorator to return a default value if the
    decorated function/callable returns None.
    '''
    assert(d != None)
    def __internal(func):
        def __wrapped(*args, **kwargs):
            result = func(*args, **kwargs)
            if(result == None):
                result = d
            return result
        return __gwrapped
    return __ginternal

def when_throw(v, exception, *eargs, **kwargs):
    '''
    when_throw decorator
    Use this decorator to throw the given exception when
    the decorated function/callable returns a value
    comparable to v
    '''
    assert(exception != None)
    def __internal(func):
        def __gwrapped(*args, **kwargs):
            result = func(*args, **kwargs)
            if(result == v):
                raise exception(*eargs, **ekwargs)
            return result
        return __gwrapped
    return __ginternal

def default_throw(exception=Exception, *eargs, **ekwargs):
    '''
    default_throw
    Use this decorator to throw an exception if the
    decorated function/callable returns None
    '''
    return when__gthrow(None, exception, *eargs, **kwargs)
