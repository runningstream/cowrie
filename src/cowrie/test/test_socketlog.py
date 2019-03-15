# -*- test-case-name: Cowrie Test Cases -*-

"""
Tests for socketlog
"""

import configparser
import json
import random
import socket
import string
import threading

from twisted.trial import unittest

from cowrie.output import socketlog

START_PORT = 53483
TIMEOUT = 5


class SocketLogTestListener(object):
    """
    The server end for the socketlog module to connect to
    """
    inst_count = 0
    def __init__(self, timeout=TIMEOUT):
        # Often trying to rebind to the same port as the last test used
        # fails, even with SO_REUSEADDR, so change the port each time
        self.listenport = START_PORT + type(self).inst_count
        type(self).inst_count += 1

        self.timeout = timeout

        self.listensock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listensock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listensock.settimeout(self.timeout)

        self.listensock.bind(("localhost", self.listenport))
        self.listensock.listen(10)

        self.connected = None
        self.connect_event = threading.Event()

    def start(self):
        """
        Kick off a listener thread for client connections
        Sets self.connected_event upon receiving a client
        """
        def _acceptConn():
            if self.connected is not None:
                raise RuntimeError("Unexpected value in self.connected")
            self.connected, self.connected_addr = self.listensock.accept()
            self.connected.settimeout(self.timeout)
            self.connect_event.set()

        listen_thread = threading.Thread(target=_acceptConn)
        listen_thread.start()

    def waitForClientConnect(self):
        """
        Wait for the client connection or time out
        """
        self.connect_event.wait(timeout=self.timeout)

    def recv(self):
        """
        Receive up to 4096 bytes from the client
        """
        return self.connected.recv(4096)

    def close(self):
        """
        Shut down
        """
        if self.connected is not None:
            self.connected.close()
            self.connected = None
        self.listensock.close()


class SocketLogTests(unittest.TestCase):
    def setUp(self):
        """
        Start up a client server, and build the configuration necessary to
        connect to it
        """
        self.listener = SocketLogTestListener()
        self.listener.start()

        self.cfg = configparser.ConfigParser()
        conf_str = u"[output_socketlog]\naddress=localhost:{}\n"\
            "timeout={}".format(self.listener.listenport, TIMEOUT)
        self.cfg.read_string(conf_str)

    def tearDown(self):
        self.listener.close()

    def initiateConnect(self):
        """
        Initiate connection to the test server

        This is not part of setUp so that if an exception is raised it will
        fail the test, not error the test.
        """
        # TODO: I don't think this is the intended use case
        socklog = socketlog.Output(cfg=self.cfg)

        # This can fail with a timeout, which means that the socketlog never
        # connected, which should fail the test.
        self.listener.waitForClientConnect()

        return socklog

    def testOutputSetup(self):
        """
        A simple test case
        """
        socklog = self.initiateConnect()

        test_data = {"output": ["this", "is", "a", "test"]}
        intended_output = json.dumps(test_data).encode()

        socklog.write(test_data)
        outval = self.listener.recv()
        self.assertEquals(outval.strip(), intended_output)

    def testOutputNormal(self):
        """
        Test case with more data
        """
        socklog = self.initiateConnect()

        def randChars(count):
            return "".join(random.choices(string.printable, k=count))

        test_data = {randChars(20): [randChars(5) for i in range(4)]
                        for j in range(10)}
        intended_output = json.dumps(test_data).encode()

        socklog.write(test_data)
        outval = self.listener.recv()
        self.assertEquals(outval.strip(), intended_output)

    def skip_testPipeBreak(self):
        """
        Test the case where some data gets sent, then the connection
        drops, and you send some more successfully
        """
        # TODO - I had a lot of trouble getting this to work
        pass
