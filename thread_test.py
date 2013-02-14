import queue
import threading
import time
import unittest


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
        def wrapped(*args, **kwargs):
            with __mutex:
                result = func(*args, **kwargs)
            return result
        return wrapped 
    return __serialize



class thread_pool(object):
    #################################################################################
    class thread_pool_stopped_exception(Exception):
        def __init__(self):
            self.message = "Cannot add new threads to a stopped thread-pool"    
    
    #################################################################################
    class thread_pool_task(object):
        def __init__(self, func, completion_handler, *args, **kwargs):
            self.__func = func
            self.__on_complete = completion_handler
            self.__args = args
            self.__kwargs = kwargs
            self.__result = None
            self.__exception = None
            self.__internal_complete = False

        def run(self):
            try:
                self.__result = self.__func(*self.__args, **self.__kwargs)
            except Exception as e:
                self.__exception = e
            self.__internal_complete = True
            self.__on_complete()

        def get(self):
            while(self.__internal_complete == False):
                time.sleep(0.01);
            if(self.__exception != None):
                raise self.__exception;
            return self.__result
    
    #################################################################################
    class thread_pool_thread(threading.Thread):
        def __init__(self, idx, pool):
            # super(self)
            threading.Thread.__init__(self, group = None, target = None, name = str(idx), 
                args = (), kwargs = {}, verbose = None)
            self.__pool = pool
            self.__complete = False
        
        def sig_complete(self):
            self.__complete = True

        def run(self):
            # process whilst our thread-pool is stil alive
            while(self.__complete != True):
                task = self.__pool.pop()
                if(task != None):
                    task.run()    
    
    ################################################################################# 
    def __init__(self, count, max_items=0):
        self.__complete = False
        self.__mutex = threading.Lock()
        self.__threads = [] 
        self.__tasks = queue.Queue(maxsize=max_items)
        self.__monitor_thread = threading.Thread(target = self.__monitor__,
                name = "ThreadPool Monitor")
        self.__min_count = count
        assert(self.__min_count != 0)
        for i in range(self.__min_count):
            thread = thread_pool.thread_pool_thread(i, self);
            self.__threads.append(thread)
            thread.start()
        self.__monitor_thread.start()
    
    def __monitor__(self):
        while(self.complete() != True):
            with self.__mutex:
                # Snap shot queue and threads.
                task_count = self.__tasks.qsize()
                thread_count = len(self.__threads)
                # If we have more tasks queued than threads
                # then generate a new thread to handle demand.
                if(task_count > thread_count):
                    try:
                        self.__add_threads(1)
                    except thread_pool_stopped_exception:
                        # Processing complete
                        pass
                # If we have no tasks and more than the minimum
                # threads then slowly contract the thread-pool
                elif((task_count == 0) and (thread_count > self.__min_count)):
                    try:
                        self.__remove_threads(1)
                    except thread_pool_stopped_exception:
                        # processing complete
                        pass
            # monitor 10 times a second
            time.sleep(0.1)

    def thread_count(self):
        with self.__mutex:
            result = len(self.__threads)
        return result

    def task_count(self):
        result = self.__queue.qsize()

    def add_threads(self, count):
        with self.__mutex:
            self.__add_threads(count)

    def __add_threads(self, count):
        if(self.complete()):
            raise thread_pool.thread_pool_stopped_exception()
        thread = thread_pool.thread_pool_thread(self._threads.count, self)
        self._threads.append(thread)
        thread.start()
    
    def remove_threads(self, count):
        with self.__mutex:
            return self.__remove_threads(count)
    
    def __remove_threads(self, count):
        if(self.complete()):
            raise thread_pool_stopped_exception()
        current = len(self.__threads)
        result = count
        if(self._min_count < (current - count)):
            result = current - self.__min_count
            
        for i in range(result):
            thread_to_dispose = self.__threads.pop()
            thread_to_dispose.sig_complete()
            thread_to_dispose.join()
            self.__threads.pop
        return result

    def process(self, func, *args, **kwargs):
        with self.__mutex:
            if(self.complete()):
                raise thread_pool.thread_pool_stopped_exception()
        
        task = thread_pool.thread_pool_task(func, self.__tasks.task_done, *args, **kwargs)
        self.__tasks.put(task, block = True)
        return task

    def pop(self):
        result = None
        try:
            result = self.__tasks.get_nowait()
        except queue.Empty: # empty queue, sleep for a bit
            time.sleep(0.01)
        return result

    def complete(self):
        return self.__complete
   
    def join(self):
        with self.__mutex:
            self.__complete = True
        
        # Drain the queue of items to be processed
        self.__tasks.join()
        self.__monitor_thread.join()
        # interupt each thread
        for t in self.__threads:
            t.sig_complete() # signal completion
            t.join() # join

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.join()

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
        except Exception as e:
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
        except no_target_exception as e:
            self.assertEqual(e.message, "No target for specified future")

    def testNoTargetNoConstruction(self):
        try:
            future(name="tester")
        except no_target_exception as e:
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
    with thread_pool(1) as tp:
        f = tp.process(test_func, 22, 2, 3, d = 4)
        print("The result is %d" % f.get())

    unittest.main()

