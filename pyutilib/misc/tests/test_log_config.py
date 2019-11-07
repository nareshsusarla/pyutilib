#  _________________________________________________________________________
#
#  PyUtilib: A Python utility library.
#  Copyright (c) 2008 Sandia Corporation.
#  This software is distributed under the BSD License.
#  Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
#  the U.S. Government retains certain rights in this software.
#  _________________________________________________________________________

import logging
import os
from inspect import currentframe, getframeinfo
from six import StringIO

import pyutilib.misc
import pyutilib.th as unittest

from pyutilib.misc.log_config import LogHandler

logger = logging.getLogger('pyutilib-testing')
filename = getframeinfo(currentframe()).filename

class TestLogging(unittest.TestCase):
    def setUp(self):
        self.stream = StringIO()

    def tearDown(self):
        logger.removeHandler(self.handler)

    def test_simple_log(self):
        # Testing positional base, configurable verbosity
        self.handler = LogHandler(
            os.path.dirname(__file__),
            stream = self.stream,
            verbosity=lambda: logger.isEnabledFor(logging.DEBUG))
        logger.addHandler(self.handler)

        logger.setLevel(logging.WARNING)
        logger.info("(info)")
        self.assertEqual(self.stream.getvalue(), "")
        logger.warn("(warn)")
        ans = "WARNING: (warn)\n"
        self.assertEqual(self.stream.getvalue(), ans)

        logger.setLevel(logging.DEBUG)
        logger.warn("(warn)")
        lineno = getframeinfo(currentframe()).lineno - 1
        ans += 'WARNING: "[base]%stest_log_config.py", %d, test_simple_log\n' \
               '    (warn)\n' % (os.path.sep, lineno,)
        self.assertEqual(self.stream.getvalue(), ans)

    def test_alternate_base(self):
        self.handler = LogHandler(
            base = 'log_config',
            stream = self.stream)
        logger.addHandler(self.handler)

        logger.setLevel(logging.WARNING)
        logger.info("(info)")
        self.assertEqual(self.stream.getvalue(), "")
        logger.warn("(warn)")
        lineno = getframeinfo(currentframe()).lineno - 1
        ans = 'WARNING: "%s", %d, test_alternate_base\n' \
               '    (warn)\n' % (filename, lineno,)
        self.assertEqual(self.stream.getvalue(), ans)

    def test_no_base(self):
        self.handler = LogHandler(
            stream = self.stream)
        logger.addHandler(self.handler)

        logger.setLevel(logging.WARNING)
        logger.info("(info)")
        self.assertEqual(self.stream.getvalue(), "")
        logger.warn("(warn)")
        lineno = getframeinfo(currentframe()).lineno - 1
        ans = 'WARNING: "%s", %d, test_no_base\n' \
               '    (warn)\n' % (filename, lineno,)
        self.assertEqual(self.stream.getvalue(), ans)

    def test_no_message(self):
        self.handler = LogHandler(
            os.path.dirname(__file__),
            stream = self.stream,
            verbosity=lambda: logger.isEnabledFor(logging.DEBUG))
        logger.addHandler(self.handler)

        logger.setLevel(logging.WARNING)
        logger.info("")
        self.assertEqual(self.stream.getvalue(), "")

        logger.warn("")
        ans = "WARNING\n"
        self.assertEqual(self.stream.getvalue(), ans)

        logger.setLevel(logging.DEBUG)
        logger.warn("")
        lineno = getframeinfo(currentframe()).lineno - 1
        ans += 'WARNING: "[base]%stest_log_config.py", %d, test_no_message\n' \
               % (os.path.sep, lineno,)
        self.assertEqual(self.stream.getvalue(), ans)

    def test_numbered_level(self):
        testname ='test_numbered_level'
        self.handler = LogHandler(
            os.path.dirname(__file__),
            stream = self.stream,
            verbosity=lambda: logger.isEnabledFor(logging.DEBUG))
        logger.addHandler(self.handler)

        logger.setLevel(logging.WARNING)
        logger.log(45, "(hi)")
        ans = "Level 45: (hi)\n"
        self.assertEqual(self.stream.getvalue(), ans)

        logger.log(45, "")
        ans += "Level 45\n"
        self.assertEqual(self.stream.getvalue(), ans)

        logger.setLevel(logging.DEBUG)
        logger.log(45, "(hi)")
        lineno = getframeinfo(currentframe()).lineno - 1
        ans += 'Level 45: "[base]%stest_log_config.py", %d, %s\n' \
               '    (hi)\n' % (os.path.sep, lineno, testname)
        self.assertEqual(self.stream.getvalue(), ans)

        logger.log(45, "")
        lineno = getframeinfo(currentframe()).lineno - 1
        ans += 'Level 45: "[base]%stest_log_config.py", %d, %s\n' \
               % (os.path.sep, lineno, testname)
        self.assertEqual(self.stream.getvalue(), ans)

    def test_long_messages(self):
        self.handler = LogHandler(
            os.path.dirname(__file__),
            stream = self.stream,
            verbosity=lambda: logger.isEnabledFor(logging.DEBUG))
        logger.addHandler(self.handler)

        msg = ("This is a long message\n\n"
               "With some kind of internal formatting\n"
               "    - including a bulleted list\n"
               "    - list 2  ")
        logger.setLevel(logging.WARNING)
        logger.warn(msg)
        ans = ( "WARNING: This is a long message\n\n"
                "    With some kind of internal formatting\n"
                "        - including a bulleted list\n"
                "        - list 2\n" )
        self.assertEqual(self.stream.getvalue(), ans)

        logger.setLevel(logging.DEBUG)
        logger.info(msg)
        lineno = getframeinfo(currentframe()).lineno - 1
        ans += ( 'INFO: "[base]%stest_log_config.py", %d, test_long_messages\n'
                 "    This is a long message\n\n"
                 "    With some kind of internal formatting\n"
                 "        - including a bulleted list\n"
                 "        - list 2\n" % (os.path.sep, lineno,))
        self.assertEqual(self.stream.getvalue(), ans)

        # test trailing newline
        msg += "\n"
        logger.setLevel(logging.WARNING)
        logger.warn(msg)
        ans += ( "WARNING: This is a long message\n\n"
                "    With some kind of internal formatting\n"
                "        - including a bulleted list\n"
                "        - list 2\n" )
        self.assertEqual(self.stream.getvalue(), ans)

        logger.setLevel(logging.DEBUG)
        logger.info(msg)
        lineno = getframeinfo(currentframe()).lineno - 1
        ans += ( 'INFO: "[base]%stest_log_config.py", %d, test_long_messages\n'
                 "    This is a long message\n\n"
                 "    With some kind of internal formatting\n"
                 "        - including a bulleted list\n"
                 "        - list 2\n" % (os.path.sep, lineno,))
        self.assertEqual(self.stream.getvalue(), ans)

        # test initial and final blank lines
        msg = "\n" + msg + "\n\n"
        logger.setLevel(logging.WARNING)
        logger.warn(msg)
        ans += ( "WARNING: This is a long message\n\n"
                "    With some kind of internal formatting\n"
                "        - including a bulleted list\n"
                "        - list 2\n" )
        self.assertEqual(self.stream.getvalue(), ans)

        logger.setLevel(logging.DEBUG)
        logger.info(msg)
        lineno = getframeinfo(currentframe()).lineno - 1
        ans += ( 'INFO: "[base]%stest_log_config.py", %d, test_long_messages\n'
                 "    This is a long message\n\n"
                 "    With some kind of internal formatting\n"
                 "        - including a bulleted list\n"
                 "        - list 2\n" % (os.path.sep, lineno,))
        self.assertEqual(self.stream.getvalue(), ans)
