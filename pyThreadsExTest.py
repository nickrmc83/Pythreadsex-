import logging
from pyThreadsEx import serialize, future, no_target_exception, thread_pool, thread_pool_full_exception, thread_pool_stopped_exception
from time import sleep
from threading import Condition, Lock
import unittest

class serialize_fixture(unittest.TestCase):
    '''
    Test fixture for serialize decorator
    '''
    class mutex_mock(object):
        def __init__(self):
            self.lock_count = 0
            self.unlock_count = 0
        def __enter__(self):
            self.lock_count = self.lock_count + 1
        def __exit__(self, *args):
            self.unlock_count = self.unlock_count + 1
    
    mutex = mutex_mock()
    
    @serialize(mutex)
    def some_method():
        pass
    
    def testLocks(self):
        # assert initial counts
        self.assertEqual(serialize_fixture.mutex.lock_count, 0)
        self.assertEqual(serialize_fixture.mutex.unlock_count, 0)

        # act
        serialize_fixture.some_method()

        # assert
        self.assertEqual(serialize_fixture.mutex.lock_count, 1)
        self.assertEqual(serialize_fixture.mutex.unlock_count, 1)

class future_fixture(unittest.TestCase):
    '''
    Test fixture for future class
    '''
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

class thread_pool_fixture(unittest.TestCase):
    '''
    Test fixture for thread-pool class
    '''

    class blocking_call(object):
        '''
        Class which blocks until condition is raised
        '''
        def __init__(self, lock):
            self.lock = lock
            logging.debug("Created blocking_call instance")

        def process(self):
            assert(self != None)
            logging.debug("entering process of blocking_call")
            try:
                with self.lock:
                    logging.debug("blocking_call acquired lock")
            except Exception as e:
                logging.debug("ERROR %s", e)

    def testConstruction(self):
        expected_threads = 10
        expected_max_tasks = 23
        with thread_pool(expected_threads, max_tasks=expected_max_tasks) as tp:
            self.assertEqual(expected_threads, tp.thread_count())
            self.assertEqual(expected_max_tasks, tp.max_tasks())
    
    def testTooManyTasksCreatesANewThread(self):
        l = Lock()
        with thread_pool(1) as tp:
            with l:
                t1 = thread_pool_fixture.blocking_call(l)
                t2 = thread_pool_fixture.blocking_call(l)
                t3 = thread_pool_fixture.blocking_call(l)
                tp.process(t1.process)
                # wait until the above process has started
                while(tp.task_count() != 0):
                    pass
                # start a second process which fills our queue
                tp.process(t2.process)
                # test a third process (the second non-live one)
                # causes a new thread to be generated
                tp.process(t3.process)
                sleep(1.0)
            # sleep so the monitor can now reduce the thread count
            # back to the minimum number
            sleep(1.0)
            tp.join()
            self.assertEqual(tp.stats()["MaxThreads"], 2)
            self.assertEqual(tp.thread_count(), 1)
    
    def testTooManyTasksThrows(self):
        l = Lock()
        with thread_pool(1, max_tasks=1) as tp:
            with l:
                t1 = thread_pool_fixture.blocking_call(l)
                t2 = thread_pool_fixture.blocking_call(l)
                t3 = thread_pool_fixture.blocking_call(l)
                tp.process(t1.process)
                # wait until the above process has started
                while(tp.task_count() != 0):
                    pass
                # start a second process which fills our queue
                tp.process(t2.process)
                # test a third process (the second non-live one)
                # causes an exception
                self.assertRaises(thread_pool_full_exception, 
                        tp.process, t3.process)
                self.assertEqual(tp.task_count(), 1)
                self.assertEqual(tp.thread_count(), 1)

if __name__ == "__main__":
    print("Beginning test run ...")
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()
