from pyThreadsEx import serialize, future, no_target_exception 
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

# with thread_pool(1) as tp:
#    f = tp.process(test_func, 22, 2, 3, d = 4)
#    print("The result is %d" % f.get())
if __name__ == "__main__":
    print("Beginning test run ...")
    unittest.main()
