#
# This file is part of Dragonfly.
# (c) Copyright 2007, 2008 by Christo Butcher
# Licensed under the LGPL.
#
#   Dragonfly is free software: you can redistribute it and/or modify it 
#   under the terms of the GNU Lesser General Public License as published 
#   by the Free Software Foundation, either version 3 of the License, or 
#   (at your option) any later version.
#
#   Dragonfly is distributed in the hope that it will be useful, but 
#   WITHOUT ANY WARRANTY; without even the implied warranty of 
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU 
#   Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public 
#   License along with Dragonfly.  If not, see 
#   <http://www.gnu.org/licenses/>.
#


import unittest
import time
import logging
from dragonfly.engines import get_engine
from dragonfly.engines.base.timer import ThreadedTimerManager


#===========================================================================

class CapturingHandler(logging.Handler):

    def __init__(self):
        logging.Handler.__init__(self)
        self.records = []

    def emit(self, record):
        self.records.append(record)


#===========================================================================

class TestTimer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # If the engine's timer manager is a ThreadedTimerManager, disable
        # the main callback to prevent race conditions.
        timer_manager = get_engine()._timer_manager
        if isinstance(timer_manager, ThreadedTimerManager):
            cls.threaded_timer_manager = timer_manager
            timer_manager.disable()
        else:
            cls.threaded_timer_manager = None

    @classmethod
    def tearDownClass(cls):
        # Re-enable the timer manager's callback if necessary.
        if cls.threaded_timer_manager:
            cls.threaded_timer_manager.enable()

    def setUp(self):
        self.log_capture = CapturingHandler()
        logging.getLogger("engine.timer").addHandler(self.log_capture)
        self.engine = get_engine()

        # Ensure the engine is connected to avoid errors.
        self.engine.connect()

    def test_timer_callback_exception(self):
        """ Test handling of exceptions during timer callback. """

        callback_called = [0]
        def callback():
            callback_called[0] += 1
            raise Exception("Exception from timer callback")

        interval = 0.01
        timer = self.engine.create_timer(callback, interval)
        time.sleep(0.02)
        timer.manager.main_callback()

        # Callback was called one or more times. The engine may or may not
        # have called it already by the time we get here, but getting an
        # exact call count is not required.
        try:
            self.assertTrue(callback_called[0] >= 1)
            self.assertTrue(len(self.log_capture.records) >= 1)
            log_message = self.log_capture.records[0].msg
            self.assertTrue("Exception from timer callback" in log_message)
        finally:
            # Stop the timer at the end regardless of the result.
            timer.stop()

    def test_non_repeating_timers(self):
        """ Test that non-repeating timers only run once. """

        callback_called = [0]
        def callback():
            callback_called[0] += 1

        interval = 0.01
        timer = self.engine.create_timer(callback, interval, False)
        time.sleep(0.02)
        timer.manager.main_callback()
        time.sleep(0.02)
        timer.manager.main_callback()

        # Callback was only called once.
        try:
            self.assertEqual(callback_called[0], 1)
        finally:
            # Stop the timer at the end regardless of the result.
            timer.stop()

#===========================================================================

if __name__ == "__main__":
    unittest.main()
