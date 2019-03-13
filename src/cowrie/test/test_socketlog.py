
"""
Tests for socketlog
"""

import configparser
import json
import socket
import threading

from twisted.trial import unittest

from cowrie.output import socketlog


PORT = 53483
TIMEOUT = 5

class SocketLogTests(unittest.TestCase):
    def setUp(self):
        self.cfg = configparser.ConfigParser()
        conf_str = "[output_socketlog]\naddress=localhost:{}\ntimeout={}".format(
            PORT, TIMEOUT)
        cfg.read_string(conf_str)

        self.listenport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listenport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Doesn't have to be same timeout as before...
        self.listenport.settimeout(TIMEOUT)

        self.listenport.bind(("localhost", PORT))
        self.listenport.listen(10)

        self.connected = None
        self.connect_event = threading.Event()

    def tearDown(self):
        self.listenport.close()

    def acceptConn(self):
        if self.connected is not None:
            raise RuntimeError("Unexpected value in self.connected")
        self.connected, self.connected_addr = self.listenport.accept()
        self.connect_event.set()

    def test_output_setup(self):
        test_data = {"output": ["this", "is", "a", "test"]}
        intended_output = json.dumps(test_data).encode()

        listen_thread = threading.Thread(target=self.acceptConn)
        listen_thread.start()

        # TODO: I don't think this is the intended use case
        socklog = socketlog.Output(cfg=self.cfg)

        # This can fail with a timeout, which should fail the test
        self.connect_event.wait(timeout=TIMEOUT)

        socklog.write(test_data)

        outval = self.connected.recv(4096)

        self.assertEquals(outval.strip(), intended_output)

    def test_output_normal(self):
        pass

    def test_output_a_lot(self):
        pass

    def test_output_pipe_breaks(self):
        pass
