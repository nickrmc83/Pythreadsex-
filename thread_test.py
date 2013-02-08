import threading
import Queue
import unittest
import time

''' 
Custom exception thrown when no target is set
upon a future.
'''
class no_target_exception(Exception):    
    def __init__(self, name=None):
        self.message = "No target for specified future"
        if(name != None):
            self.message = self.message + " (" + name + ")"

    def __str__(self):
        return self.message

'''
Custom decorator which allows serialised access to a function
'''
def serialize(__mutex):
    assert(__mutex != None)
    def __serialize(func):
        def wraped(*args):
            __mutex.acquire()
            try:
                result = func(*args)
            finally:
                __mutex.release()
            return result
        return wraped 
    return __serialize



class thread_pool(object):
    #################################################################################
    class thread_pool_task(object):
        def __init__(self, func, complete, *args, **kwargs):
            self.func = func
            self.complete = complete
            self.args = args
            self.kwargs = kwargs
            self.result = None
            self.exception = None
            self.__internal_complete = False

        def run(self):
            try:
                self.result = self.func(*self.args, **self.kwargs)
            except Exception, e:
                self.exception = e
            self.complete()
            self.__internal_complete = True

        def get(self):
            while(self.__internal_complete == False):
                time.sleep(0.01);
            if(self.exception != None):
                raise self.exception;
            return self.result
    #################################################################################
    class thread_pool_thread(threading.Thread):
        def __init__(self, idx, pool):
            # super(self)
            threading.Thread.__init__(self, group = None, target = None, name = str(idx), 
                args = (), kwargs = {}, verbose = None)
            self.pool = pool

        def run(self):
            while(self.pool.complete() != True):
                task = self.pool.pop()
                if(task != None):
                    task.run()    
    ################################################################################# 

    def __init__(self, count):
        self.__complete = False
        self.__threads = [] 
        self.__tasks = Queue.Queue()
        for i in range(count):
            thread = thread_pool.thread_pool_thread(i, self);
            self.__threads.append(thread)
            thread.start()

    def process(self, func, *args, **kwargs):
        task = thread_pool.thread_pool_task(func, self.__tasks.task_done, *args, **kwargs)
        self.__tasks.put(task, block = True)
        return task

    def pop(self):
        result = None
        try:
            result = self.__tasks.get(block = False)
        except Queue.Empty:
            time.sleep(0.01)
        return result

    def complete(self):
        return self.__complete

    def join(self):
        self.__tasks.join()
        self.__complete = True
        for t in self.__threads:
            t.join()

'''
A future allows the evaluation of a target asynchronously.
The result of the asynchronous calculation can be accessed
using the get() method. If an exception is thrown during
the evaluation of the target, the exception will be
re-thrown from the get() method.
'''
class future(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
            args=(), kwargs={}, verbose=None):
        threading.Thread.__init__(self, group, target, name, 
                args, kwargs, verbose)
        if(target == None):
            raise no_target_exception(name)
        self.__target = target
        self.__args = args
        self.__kwargs = kwargs
        self.__retval = None # return value
        self.__excepton = None # internal exception
        self.start()

    # override the thread run method
    def run(self):
        try:
            self.__retval = self.__target(*self.__args, **self.__kwargs)
        except Exception, e:
            self.__exception = e

    # return the result of the asynchronous calculation
    def get(self, timeout=None):
        self.join(timeout)
        if(self.__retval != None):
            return self.__retval;
        if(self.__exception != None):
            raise self.__exception

class future_fixture(unittest.TestCase):
    def __add(self, a, b):
        return a + b

    def testNoTargetNoConstruction(self):
        try:
            future()
        except no_target_exception, e:
            self.assertEqual(e.message, "No target for specified future")

    def testNoTargetNoConstruction(self):
        try:
            future(name="tester")
        except no_target_exception, e:
            self.assertEqual(e.message, "No target for specified future (tester)")

    def testConstructor(self):
        f = future(target=self.__add)

    def testExecute(self):
        f = future(target=self.__add, args=(10,12))
        self.assertEqual(f.get(), 22)

def test_func(a, b, c, d = None):
    print("processing test_func")
    return a + b + c + d

# main function
if __name__ == "__main__":
    tp = thread_pool(5)
    f = tp.process(test_func, 22, 2, 3, d = 4)
    print("The result is %d" % f.get())
    tp.join()
    unittest.main()

