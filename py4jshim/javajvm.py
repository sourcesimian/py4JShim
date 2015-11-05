import os
import shutil
import subprocess
import tempfile
import signal
import uuid

_py4j_jar = 'py4j0.9.jar'
_stub_name = 'Py4JStub'

from py4j.java_gateway import JavaGateway, GatewayClient, java_import

_java_stub_template = """\
import py4j.GatewayServer;

public class Py4JStub {
    public Py4JStub () {
    }

    public static void main(String[] args) {
        System.out.println("Starting Py4J GatewayServer on %(port)d");

        class EntryPoint {
            final String id = "%(id)s";

            public EntryPoint() {
            }

            public String getId() {
                return id;
            }
        }

       GatewayServer gatewayServer = new GatewayServer(new EntryPoint(), %(port)d);
       gatewayServer.start();
    }
}
"""


class JavaJVM(object):
    __instance = 0
    __port = 25335
    __temp_dir = None
    __p = None
    __id = None

    def __init__(self, class_paths):
        self.__port += self.__instance
        JavaJVM.__instance += 1
        self.__id = str(uuid.uuid4())
        self.__class_paths = class_paths or []
        self.__init_paths()
        self.__compile_stub()
        self.__p = self.__launch_process()
        gc = GatewayClient(port=self.__port)
        self.__gw = JavaGateway(gc, start_callback_server=True)
        assert self.__gw.entry_point.getId() == self.__id, "Did not connect to the expected gateway"

    def __del__(self):
        try:
            if self.__temp_dir:
                shutil.rmtree(self.__temp_dir)
            self.__gw.shutdown()
            if self.__p:
                os.kill(self.__p.pid, signal.SIGTERM)
        except OSError:
            pass

    def java_import(self, import_str):
        java_import(self.__gw.jvm, import_str)

    @property
    def jvm(self):
        return self.__gw.jvm

    @property
    def pid(self):
        return self.__p.pid

    @property
    def id(self):
        return self.__gw.entry_point.getId()

    def __getattr__(self, name):
         return self.__gw.jvm.__getattr__(name)

    def __init_paths(self):
        mod = __import__('py4j', globals(), locals(), level=-1)
        py4j_dir = os.path.split(mod.__file__)[0]
        self.__py4j_jar = os.path.join(py4j_dir, '../../../../share/py4j', _py4j_jar)

    def __compile_stub(self):
        self.__temp_dir = tempfile.mkdtemp(prefix='py4j.')

        stub = os.path.join(self.__temp_dir, _stub_name)
        with open(stub + '.java', 'wb') as f:
            ctx = {}
            ctx['port'] = self.__port
            ctx['id'] = self.__id
            f.write(_java_stub_template % ctx)

        class_paths = []
        class_paths.append('.')
        class_paths.append(self.__py4j_jar)
        class_paths.extend(self.__class_paths)

        self._compile_java(self.__temp_dir, _stub_name, class_paths)

    def __launch_process(self):
        class_paths = []
        class_paths.append('.')
        class_paths.append(self.__py4j_jar)
        class_paths.extend(self.__class_paths)

        return self._launch_java(self.__temp_dir, _stub_name, class_paths)

    @classmethod
    def _compile_java(cls, cwd, class_path, class_paths):
        base_file = os.path.join(*class_path.split('.'))
        java_file = base_file + '.java'
        java_path = os.path.join(cwd, base_file + '.java')
        class_path = os.path.join(cwd, base_file + '.class')

        if not os.path.isfile(class_path) or \
           os.stat(java_path).st_mtime > os.stat(class_path).st_mtime:

            args = [
                'javac',
                '-cp',
                ':'.join(class_paths),
                java_file
            ]
            p = subprocess.Popen(args=args, cwd=cwd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            p.wait()
            if not p.returncode == 0:
                raise IOError('Unable to compile %s\ncwd: %s\ncmd: %s\nerr: %s' %
                              (class_path, cwd, ' '.join(args), p.stderr.read()))

    @classmethod
    def _launch_java(cls, cwd, class_path, class_paths):
        base_file = os.path.join(*class_path.split('.'))

        args = [
            'java',
            '-cp',
            ':'.join(class_paths),
            base_file,
        ]

        p = subprocess.Popen(args=args, cwd=cwd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        import time
        time.sleep(1)
        if p.returncode is not None:
                raise IOError('Could not start %s\ncwd: %s\ncmd: %s\nerr: %s' %
                              (class_path, cwd, ' '.join(args), p.stderr.read()))
        return p


__all__ = ['JavaJVM']