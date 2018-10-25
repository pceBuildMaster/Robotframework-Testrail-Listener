import os
import signal
from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn
from TestRailAPIClient import TestRailAPIClient
from TestRailAPIClient import TestRailAPIError

# import Testrail server info
try:
    from  TestRailServer import TESTRAIL_SERVER
    from  TestRailServer import TESTRAIL_PROTOCOL
    from  TestRailServer import TESTRAIL_PROJECT_ID
    from  TestRailServer import TESTRAIL_USER
    from  TestRailServer import TESTRAIL_PW
except ImportError as e:
    raise ValueError('TestRail server info not found in TestRailServer.py.  Error: {}'.format(e))


class TestRailListener(object):

    '''
    Use Robot Framework's Listener interface to add results from test runs to TestRail.

    RF Listener events:

    start_suite():
        Log current suite being run and push suite onto queue

    start_test():
        Log current test being run

    end_test():
        Log result of test being run

    suite_end():
        Pop suite from queue

    close():
        Log log if enabled.
    '''

    ROBOT_LISTENER_API_VERSION = 2


    def __init__(self):
        # logging
        self.logger = ListenerLogger()
        self.logname = 'tr_listener.log'

        # suite queue and map
        self.suite_queue = SuiteQueue()

        # Set testrail server info
        try:
            self.project_id = TESTRAIL_PROJECT_ID
            self.testrail_server = TESTRAIL_SERVER
            self.testrail_user = TESTRAIL_USER
            self.testrail_password = TESTRAIL_PW
            protocol = TESTRAIL_PROTOCOL
        except NameError as e:
            raise ValueError('TestRail server info not found. Ensure TestRailServer.py exists and has needed info.  Error: {}'.format(e))
            self.signal_quit()

        if self.testrail_server is not None:
            self.testrail = TestRailAPIClient(
                    self.testrail_server,
                    protocol=protocol,
                    user=self.testrail_user,
                    password=self.testrail_password)
            self.auto_type = self.testrail.get_automated_test_case_type()
            self.user_id = self.testrail.get_user_id(self.testrail_user)
        else:
            self.testrail = None
            self.auto_type = None
            self.user_id = None

    def start_suite(self, name, attrs):
        if 's1' == attrs['id']:
            # first suite encountered. open Listener log in RF output dir and connect to Testrail.
            # must be done here on first suite event and not in __init__ as BuiltIn cannot be
            # accessed until in a test context
            self.logger.open(self.logname)
            tr_section_id, msg = self.init_testrail_testsuite(name)
        else:
            if 's1-s1' == attrs['id']:
                # second suite encountered. top level RF suite setup has been executed so init data that is based
                # on what top level RF suite setup has set from actual test run.
                self.init_site_specific_info()
            # get TR section ID based on RF suite name
            tr_section_id, msg = self.init_testrail_section(name)
        self.logger.log(msg)
        self.suite_queue.push(name, tr_section_id)

    def start_test(self, name, attrs):
        self.logger.log('{}.{} - '.format(self.suite_queue.current_path(), name))

    def end_test(self, name, attrs):
        # set testrail Result data from RF attrs
        result_id = [attrs['status']]
        msg = attrs['message'] if attrs['message'] else None
        elapsed_secs = attrs['elapsedtime'] / 1000
        duration = '{}s'.format(elapsed_secs) if elapsed_secs > 0 else '1s'
        self.logger.log('{} [{}] ({})\n'.format(attrs['status'], duration, msg))

    def end_suite(self, name, attrs):
        self.suite_queue.pop()
        self.logger.log('{}\n'.format(self.suite_queue.current_path()))

    def close(self):
        self.logger.close()

    def init_site_specific_info(self):
        '''
        Example site specific info.

        For this context setting names of TR Milestone, Plan, and Run for results can
        be done here based on run data set in top-level RF suite setup.

        Example:

        self.milestone = '{} - {}'.format(BuiltIn().get_variable_value("$MODEL"),
                                          BuiltIn().get_variable_value("$VERSION"))
        '''
        pass

    def init_testrail_testsuite(self, rf_top_level_suite_name):
        # in full implementaion make TR api calls to get/create Test Suite
        msg = 'Using RF testsuite: {}\n\nSuites:\n{}\n'.format(rf_top_level_suite_name, rf_top_level_suite_name)
        return 0, msg

    def init_testrail_section(self, rf_suite_name):
        # in full implementaion make TR api calls to get/create test Section
        msg = '{}.{}\n'.format(self.suite_queue.current_path(), rf_suite_name)
        return 1 + self.suite_queue.current_id(), msg

    def signal_quit(self):
        self.logger.log('Sending SIGINT from Listener to abort test run\n')
        os.kill(os.getpid(), signal.SIGINT)
        # graceful shutdown is too slow and allows code to run after
        # previous fatal error. so send another to abort abruptly.
        os.kill(os.getpid(), signal.SIGINT)


class ListenerLogger(object):


    def __init__(self, enabled=True):
        self.logging_enabled = enabled
        self._log_handle = None

    def open(self, filename):
        if self.logging_enabled:
            # create log file in RF output dir
            logname = '{}/{}'.format(BuiltIn().get_variable_value("$outputdir"), filename)
            self._log_handle = open(logname, 'w')

    def log(self, msg, console=False):
        if self._log_handle is not None:
            self._log_handle.write(msg)
        if console:
            self.log_console(msg)

    def log_console(self, msg):
            logger.console(msg)

    def close(self):
        if self._log_handle is not None:
            self._log_handle.close()


class SuiteQueue(object):


    def __init__(self):
        # use list as queues
        self._suites = []    # RF suite name queue. suite names as they are seen
        self._suite_ids = [] # TR section ID queue. testsuite section ID mapping to rf suite name

    def push(self, rf_suite_name, tr_section_id):
        self._suites.append(rf_suite_name)
        self._suite_ids.append(tr_section_id)

    def pop(self):
        self._suites.pop()
        self._suite_ids.pop()

    def current_id(self):
        # last ID pushed on queue is current suite ID
        return self._suite_ids[-1]

    def current_path(self):
        # string of all suite names currently in queue
        return '.'.join(self._suites)

