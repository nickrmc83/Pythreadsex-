from logging import debug
from queue import Queue, Empty, Full
from threading import Thread, Lock
from time import sleep


def serialize(__mutex):
    '''
    Custom decorator which allows serialised access to a function
    using a mutex.
    '''   
    assert(__mutex != None)
    def __serialize(func):
        def wrapped(*args, **kwargs):
            with __mutex:
                result = func(*args, **kwargs)
            return result
        return wrapped 
    return __serialize

class thread_pool_stopped_exception(Exception):
    '''
    This exception class is thrown when any attempt to
    use a stopped thread-pool is attempted.
    '''
    "Cannot add new threads to a stopped thread-pool."

class thread_pool_full_exception(Exception):
    '''
    This exception class is thrown when any attempt to
    add a new task to a thread-pool which is full happens.
    '''
    "Cannot add new task to thread-pool as it is full."

class thread_pool(object):
    '''
    Thread-pool implementation which has the following features:
        - Dynamic scaling of threads-to-work load
        - Implementation of thread-pool tasks which are akin to
          futures.
        - Fully join-able
    '''
    
    ############################################################################
    class thread_pool_task(object):
        '''
        A thread-pool task is a single unit of work to be undertaken
        by a thread-pool. When a task is queued on a thread-pool a
        handle to a thread-pool task is returned which acts to the caller
        as a future. The result of the task performed maybe accessed
        by the blocking get() call
        '''
        def __init__(self, tid, func, completion_handler, *args, **kwargs):
            self.__tid = tid
            self.__func = func
            self.__on_complete = completion_handler
            self.__args = args
            self.__kwargs = kwargs
            self.__result = None
            self.__exception = None
            self.__internal_complete = False

        def run(self):
            debug("Starting execution of task %d" % self.__tid)
            try:
                self.__result = self.__func(*self.__args, **self.__kwargs)
            except Exception as e:
                self.__exception = e
                debug("Exception %s thrown when executing task %d." % (e, self.__tid))
            self.__internal_complete = True
            self.__on_complete()
            debug("Completed task %d" % self.__tid)

        def get(self):
            while(self.__internal_complete == False):
                sleep(0.01);
            if(self.__exception != None):
                raise self.__exception;
            return self.__result
    
    ############################################################################
    class thread_pool_thread(Thread):
        '''
        This class represents a single thread-pool thread owned by a thread-pool
        '''
        def __init__(self, idx, pool):
            # super(self)
            Thread.__init__(self, group = None, target = None, name = str(idx), 
                args = (), kwargs = {})
            self.__pool = pool
            self.__complete = False
        
        def sig_is_complete(self):
            self.__complete = True

        def run(self):
            # process whilst our thread-pool is stil alive
            while(self.__complete != True):
                task = self.__pool.pop()
                if(task != None):
                    task.run()    
    
    ############################################################################
    def __init__(self, count, max_tasks=0):
        self.__complete = False
        self.__mutex = Lock()
        self.__next_tid = 1
        self.__threads = [] 
        self.__tasks = Queue(maxsize=max_tasks)
        self.__monitor_thread = Thread(target = self.__monitor__,
                name = "ThreadPool Monitor")
        self.__min_thread_count = count
        self.__most_thread_count = self.__min_thread_count
        self.__total_tasks = 0
        assert(self.__min_thread_count != 0)
        for i in range(self.__min_thread_count):
            thread = thread_pool.thread_pool_thread(i, self);
            self.__threads.append(thread)
            thread.start()
        self.__monitor_thread.start()
    
    def stats(self):
        '''
        Return a dictionary of statistics about the thread-pool
        '''
        result = {"MinThreads" : self.__min_thread_count,
                "MaxThreads" : self.__most_thread_count,
                "TaskCount" : self.__tasks.qsize()}
        return result
        
    def __monitor__(self):
        while(self.is_complete() != True):
            with self.__mutex:
                # Snap shot queue and threads.
                task_count = self.__tasks.qsize()
                thread_count = len(self.__threads)
                # If we have more tasks queued than threads
                # then generate a new thread to handle demand.
                if(task_count > thread_count):
                    debug("Adding new thread in monitor: tasks = %d, threads = %d" 
                            % (task_count, thread_count)) 
                    try:
                        self.__add_threads(1)
                    except thread_pool_stopped_exception:
                        # Processing complete
                        pass
                # If we have no tasks and more than the minimum
                # threads then slowly contract the thread-pool
                elif((task_count == 0) and (thread_count > self.__min_thread_count)):
                    debug(
                            "Removing existing thread in monitor: tasks = %d, threads = %d" 
                            % (task_count, thread_count))
                    try:
                        self.__remove_threads(1)
                    except thread_pool_stopped_exception:
                        # processing complete
                        pass
            # monitor once a second
            sleep(1.0)

    def thread_count(self):
        with self.__mutex:
            result = len(self.__threads)
        return result

    def max_tasks(self):
        return self.__tasks.maxsize

    def task_count(self):
        return self.__tasks.qsize()

    def add_threads(self, count):
        with self.__mutex:
            self.__add_threads(count)

    def __add_threads(self, count):
        if(self.is_complete()):
            raise thread_pool.thread_pool_stopped_exception()
        thread = thread_pool.thread_pool_thread(self.__threads.count, self)
        self.__threads.append(thread)
        thread.start()
        thread_count = len(self.__threads)
        if(thread_count > self.__most_thread_count):
            self.__most_thread_count = thread_count

    def remove_threads(self, count):
        with self.__mutex:
            return self.__remove_threads(count)
    
    def __remove_threads(self, count):
        if(self.is_complete()):
            raise thread_pool_stopped_exception()
        current = len(self.__threads)
        result = count
        if(self.__min_thread_count < (current - count)):
            result = current - self.__min_thread_count
            
        for i in range(result):
            thread_to_dispose = self.__threads.pop()
            thread_to_dispose.sig_is_complete()
            thread_to_dispose.join()
        return result

    def process(self, func, *args, **kwargs):
        tid = 0
        with self.__mutex:
            if(self.is_complete()):
                raise thread_pool.thread_pool_stopped_exception()
            tid = self.__next_tid
            self.__next_tid = self.__next_tid + 1
            debug("Adding new thread-pool task. %d already queued." % self.task_count())
        try:
            task = thread_pool.thread_pool_task(tid, func, self.__tasks.task_done, *args, **kwargs)
            if(self.__tasks.maxsize == 0):
                block = True
            else:
                block = False;
            debug("Queueing task with blocking as %d" % block)
            self.__tasks.put(task, block = block)
        except Full:
            debug("Failed to add task %d as task queue full" % tid)
            raise thread_pool_full_exception()
        return task

    def pop(self):
        result = None
        try:
            result = self.__tasks.get(timeout=0.01)
        except Empty: # empty queue, ignore
            pass
        return result

    def is_complete(self):
        return self.__complete
   
    def join(self):
        with self.__mutex:
            self.__complete = True
        
        # Drain the queue of items to be processed
        self.__tasks.join()
        self.__monitor_thread.join()
        # interupt each thread
        for t in self.__threads:
            t.sig_is_complete() # signal completion
            t.join() # join

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.join()

class no_target_exception(Exception):    
    ''' 
    Custom exception thrown when no target is set
    upon a future.
    '''   
    def __init__(self, name=None):
        self.message = "No target for specified future"
        if(name != None):
            self.message = self.message + " (" + name + ")"

class future(Thread):
    '''
    A future allows the evaluation of a target asynchronously.
    The result of the asynchronous calculation can be accessed
    using the get() method. If an exception is thrown during
    the evaluation of the target, the exception will be
    re-thrown from the get() method.
    '''
    def __init__(self, group=None, target=None, name=None,
            args=(), kwargs={}):
        if(target == None):
            raise no_target_exception(name)
        Thread.__init__(self, group, target, name, 
                args, kwargs)
        
        self.__target = target
        self.__args = args
        self.__kwargs = kwargs
        self.__retval = None # return value
        self.__excepton = None # internal exception
        self.start()

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

    def __enter__(self):
        return self

    def __exit__(*args, **kwargs):
        self.get()
