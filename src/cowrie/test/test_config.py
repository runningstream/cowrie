
"""
This module tests config.py
"""

import os
import tempfile

from twisted.trial import unittest

from cowrie.core import config


class ConfigTester(unittest.TestCase):
    def testConfig(self):
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            os.mkdir("etc")
            with open("etc/cowrie.cfg.dist", "w") as dist_file:
                dist_file.write("[dist_config]\noption=foobar\n\n"
                                "[to_override]\nover_option=dist_version\n")
            with open("etc/cowrie.cfg", "w") as local_file:
                local_file.write("[to_override]\nover_option=local_version\n")

            self.assertEquals(
                    [os.path.join(tempdir, "etc/cowrie.cfg.dist"),
                         os.path.join(tempdir, "etc/cowrie.cfg")],
                    config.get_config_path())

            config_val = config.readConfigFile(config.get_config_path())

            intended_config = {
                    "dist_config": {"option": "foobar"},
                    "to_override": {"over_option": "local_version"}
                }

            for section in intended_config.keys():
                for option in intended_config[section].keys():
                    self.assertEquals(intended_config[section][option],
                         config_val.get(section, option))
