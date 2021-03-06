from TestRailAPIClient import TestRailAPIError
from TestRailListener import TestRailListener

# import site specific function
# used to define the names used in Testrail for Milestone, Plan, and Run from an RF test run
try:
    from  TestRailServer import set_testrail_names
except ImportError as e:
    raise ValueError('Function to set TestRail name not found in TestRailServer.py.  Error: {}'.format(e))


# used for running debugger:
#import sys
#import pdb
#pdb.Pdb(stdout=sys.__stdout__).set_trace()


class TestRailRunListener(TestRailListener):

    '''
    Use Robot Framework's (RF) Listener interface to add results from test runs to TestRail(TR).

        TR Tests are added as each new RF suite is run.  Followed by adding TR Result after each RF test.

        Listener logs progress to a file in the RF output dir.


    RF Listener events:

    start_suite():
        Push RF suite name and its Testrail Testsuite section ID to queue.  This is used to map RF to TR.

        If suite has actual tests add them to TR Plan entry Run. If first RF tests then add TR Run entry to Plan.
        As TR Tests are added to Run update map of RF-test-title to TR-Case-ID.

        On first RF suite add TR Testsuite ID to progress queue instead of a TR section ID, and run other
        initializations tasks.  Top level Suite Setup has NOT been called yet as start_suite() is
        called before all suite setups.

        On second suite top level Suite Setup has been run so initialize TR entries Milestone and Plan that
        results will be added to. Names used will be based on TR variables created by RF top level suite.
        This logic will need to be customized for each TR/RF install.

    start_test():
       (From parent class) Log current test being run

    end_test():
        Add RF result to TR Test Case.

    suite_end():
        Pop suite from queue

    close():
        Log log if enabled.
    '''

    ROBOT_LISTENER_API_VERSION = 2


    def __init__(self):
        # init parent
        super(TestRailRunListener, self).__init__()

        # map of RF test title to TR Case ID
        # dict of dict of RF test names to TestRail Case IDs stored by [suite_id][title]
        self.title2caseid = {}

        # Testrail info
        self.testsuite_id = None
        self.milestone = None
        self.milestone_id = None
        self.plan = None
        self.plan_id = None
        self.run = None
        self.run_id = None
        self.entry_id = None
        self.result_status_ids = {'PASS': 1, 'FAIL': 5}


    def start_suite(self, name, attrs):
        if 's1' == attrs['id']:
            # first suite encountered. open Listener log in RF output dir and connect to Testrail.
            # must be done here on first suite event and not in __init__ as BuiltIn cannot be
            # accessed until in a test context
            self.logger.open(self.logname)
            tr_section_id, msg = self.init_testrail_testsuite(name)
            tests = attrs['tests']
        else:
            if 's1-s1' == attrs['id']:
                # second suite encountered. top level RF suite setup has been executed. so init Listener data
                # that is based on what top level RF suite setup has set from actual test run.
                self.init_site_specific_info()
                self.init_testrail_milestone()
                self.init_testrail_plan()
                self.logger.log('\nSuites:\n{}\n'.format(self.suite_queue.current_path()))
            # get tr section ID based on RF suite name
            tr_section_id, tests, msg = self.init_testrail_section(name, attrs['tests'])
        self.logger.log(msg)
        self.suite_queue.push(name, tr_section_id)
        # process this suite's data and tests if they exist
        self.add_rf_suite_tests_to_tr_run(tr_section_id, tests)

    def end_test(self, name, attrs):
        # set TR Result data from RF attrs
        result_id = self.result_status_ids[attrs['status']]
        msg = attrs['message'] if attrs['message'] else None
        elapsed_secs = attrs['elapsedtime'] / 1000
        duration = '{}s'.format(elapsed_secs) if elapsed_secs > 0 else '1s'

        # get TR Case ID from RF test name
        section_id = self.suite_queue.current_id()
        try:
            case_id = self.title2caseid[section_id][name]
        except KeyError:
            # log but do not quit.
            self.logger.log('{} [{}] ({}) - failed to get case ID\n'.format(attrs['status'], duration, msg))
            return

        # add TR Result
        try:
            resp = self.testrail.add_result_for_case(self.run_id, case_id, result_id,
                    elapsed=duration, comment=msg)
        except TestRailAPIError as e:
            # log but do not quit.
            self.logger.log('failed to update - {} [{}] ({})\n'.format(attrs['status'], duration, msg))
            self.logger.log('\tLISTENER ERROR: add result for case error: [{}: {}]\n'.format(e.code, e.error), console=True)
            return
        self.logger.log('{} [{}] ({})\n'.format(attrs['status'], duration, msg))

    def init_site_specific_info(self):
        '''
        This method calls a function defined in TestRailServer.py.
        This allows site specific details to be defined outside the class code.
        '''
        self.milestone, self.plan, self.run = set_testrail_names(self.logger)

    def init_testrail_milestone(self):
        # get milestone ID if it already exists
        try:
            milestones = self.testrail.get_milestones(self.project_id)
        except TestRailAPIError as e:
            self.logger.log('LISTENER FATAL ERROR: get milestones error: {}: {}\n'.format(e.code, e.error), console=True)
            self.signal_quit()
        for m in milestones:
            if self.milestone == m['name'] and not m['is_completed']:
                self.milestone_id = m['id']

        # create it if it does not exist or is already completed/closed
        created = ''
        if self.milestone_id is None:
            try:
                resp = self.testrail.add_milestone(self.project_id, self.milestone)
            except TestRailAPIError as e:
                self.logger.log('LISTENER FATAL ERROR: add milestone error: {}: {}\n'.format(e.code, e.error), console=True)
                self.signal_quit()
            self.milestone_id = resp['id']
            created = ' - created ({})'.format(self.milestone_id)
        self.logger.log(' - Using Testrail Milestone [{}]{}\n'.format(self.milestone, created))

    def init_testrail_plan(self):
        # get Plan ID if it already exists
        try:
            plans = self.testrail.get_plans(self.project_id, milestone_id=self.milestone_id)
        except TestRailAPIError as e:
            self.logger.log('LISTENER FATAL ERROR: get plans error: {}: {}\n'.format(e.code, e.error), console=True)
            self.signal_quit()
        for p in plans:
            if self.plan == p['name'] and not p['is_completed']:
                self.plan_id = p['id']

        # create it if it does not exist or already closed
        created = ''
        if self.plan_id is None:
            try:
                resp = self.testrail.add_plan(self.project_id, self.plan, milestone_id=self.milestone_id)
            except TestRailAPIError as e:
                self.logger.log('LISTENER FATAL ERROR: add plan error: {}: {}\n'.format(e.code, e.error), console=True)
                self.signal_quit()
            self.plan_id = resp['id']
            created = ' - created ({})'.format(self.plan_id)
        self.logger.log(' - Using Testrail Plan [{}]{}\n'.format(self.plan, created))

    def init_testrail_testsuite(self, rf_top_level_suite_name):
        # get TR Testsuite ID used for this Run
        try:
            tr_suites = self.testrail.get_suites(self.project_id)
        except TestRailAPIError as e:
            self.logger.log('LISTENER FATAL ERROR: get test suites error: {}: {}\n'.format(e.code, e.error), console=True)
            self.signal_quit()
        for s in tr_suites:
            if rf_top_level_suite_name == s['name']:
                self.testsuite_id = s['id']

        # testsuite must already exist
        if self.testsuite_id is None:
            self.logger.log('LISTENER FATAL ERROR: Failed to find ID for Testrail test suite [{}]\n'.format(rf_top_level_suite_name), console=True)
            self.signal_quit()
        return self.testsuite_id, 'Adding test results to Testrail from running RF testsuite: {}\n'.format(
                rf_top_level_suite_name)

    def init_testrail_section(self, rf_suite_name, tests):
        # last TR section ID pushed to suite queue is the parent of this RF suite name being processed.
        # but if that ID is also the testrail testsuite ID then this section has no parent id to be
        # found or created under.
        cur_parent_id = self.suite_queue.current_id()
        if cur_parent_id == self.testsuite_id:
            cur_parent_id = None

        # get all TR sections in testsuite
        try:
            tr_sections = self.testrail.get_sections(self.project_id, self.testsuite_id)
        except TestRailAPIError as e:
            self.logger.log('LISTENER FATAL ERROR: get sections error: {}: {}\n'.format(e.code, e.error), console=True)
            self.signal_quit()

        # find current section ID if it exists ensuring parent_id is correct.
        # tr_section['parent_id'] will be None if this is a top-level TR section.
        # this is so sections with the same name but in different places do not get
        # used just because they were seen first.
        tr_section_id = None
        for tr_section in tr_sections:
            if rf_suite_name == tr_section['name'] and cur_parent_id == tr_section['parent_id']:
                tr_section_id = tr_section['id']

        # should exist
        msg = '{}.{}'.format(self.suite_queue.current_path(), rf_suite_name)
        if tr_section_id is not None:
            return tr_section_id, tests, '{}\n'.format(msg)
        else:
            # log but do not quit run. return empty test case list to prevent attempt to add them to test run
            self.logger.log_console('\nLISTENER ERROR: Failed to find Testrail section [{}]\n'.format(rf_suite_name))
            return None, [], '{} - failed to get section id\n'.format(msg)

    def add_rf_suite_tests_to_tr_run(self, tr_section_id, rf_tests):
        if not rf_tests:
            # no tests in this suite to add
            return

        # get testrail Case from TR Section ID mapped to RF suite name
        try:
            tr_cases = self.testrail.get_cases(self.project_id, self.testsuite_id, tr_section_id)
        except TestRailAPIError as e:
            self.logger.log('LISTENER FATAL ERROR: get test cases error: {}: {}\n'.format(e.code, e.error), console=True)
            self.signal_quit()

        # get the list of TR Case IDs. also update RF-test-title to TR-section-title map.
        self.title2caseid[tr_section_id] = {}
        tr_case_ids = []
        for rf_title in rf_tests:
            for tr_case in tr_cases:
                tr_title = tr_case['title']
                if rf_title == tr_title:
                    tr_case_id = tr_case['id']
                    tr_case_ids.append(tr_case_id)
                    self.title2caseid[tr_section_id][tr_title] = tr_case_id

        # add/update TR Run in Plan
        if self.run_id is None:
            # first test cases so add to Plan a test Run entry with these TR Case IDs
            try:
                resp = self.testrail.add_plan_entry(self.plan_id, self.testsuite_id, self.run,
                        case_ids=tr_case_ids, include_all=False, assignedto_id=self.user_id)
            except TestRailAPIError as e:
                self.logger.log('LISTENER FATAL ERROR: add plan entry error: {}: {}\n'.format(e.code, e.error), console=True)
                self.signal_quit()

            # TR api response is just the entry in the Plan so this is the easiest time to
            # get the entry ID and Run ID.  Note this assumes for now that TR Configurations
            # are not used so there is only one Run in the Plan entry
            self.run_id = resp['runs'][0]['id']
            self.entry_id = resp['id']
            created = ' - created ({})'.format(self.run_id)
            self.logger.log(' - Using Testrail Run [{}] - created ({})\n'.format(self.run, self.run_id))
        else:
            # just update existing test run
            try:
                resp = self.testrail.update_plan_entry(self.plan_id, self.entry_id,
                        run_id=self.run_id, case_ids=tr_case_ids)
            except TestRailAPIError as e:
                self.logger.log('LISTENER FATAL ERROR: update plan entry error: {}: {}\n'.format(e.code, e.error), console=True)
                self.signal_quit()

