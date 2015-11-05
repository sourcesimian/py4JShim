import unittest
import os

from py4jshim.javajvm import JavaJVM


class Py4JShimTest(unittest.TestCase):
    def setUp(self):
        self.__compile_java('hello.HelloWorld')

    def tearDown(self):
        pass

    def __compile_java(self, class_path):
        self.__java_base = os.path.split(__file__)[0]
        JavaJVM._compile_java(self.__java_base, class_path, [])

    def test_basic(self):
        class_paths = [self.__java_base]
        jvm = JavaJVM(class_paths)
        print jvm.pid
        print jvm.id

    def test_many(self):
        class_paths = [self.__java_base]
        j = JavaJVM(class_paths)
        k = JavaJVM(class_paths)
        l = JavaJVM(class_paths)

        j.java_import('hello.HelloWorld1')
        J = j.hello.HelloWorld()

        K = k.hello.HelloWorld()

        L = l.hello.HelloWorld()
        L2 = l.hello.HelloWorld()

        J.setMessage('J')
        K.setMessage('K')
        L.setMessage('L')
        L2.setMessage('L2')

        self.assertEqual('J', J.getMessage())
        self.assertEqual('K', K.getMessage())
        self.assertEqual('L', L.getMessage())
        self.assertEqual('L2', L2.getMessage())

        random = j.jvm.java.util.Random()   # create a java.util.Random instance
        number1 = random.nextInt(10)        # call the Random.nextInt method
        number2 = random.nextInt(10)
        print number1, number2

        print k, l

    def test_jvm(self):
        class_paths = [self.__java_base]
        j = JavaJVM(class_paths)

        j.java_import('hello.*')
        h = j.HelloWorld()

        print h.getMessage()


