from TestRailAPIClient import TestRailAPIError
from TestRailListener import TestRailListener


class TestRailCasesListener(TestRailListener):


    ROBOT_LISTENER_API_VERSION = 2


    def __init__(self):
        # init parent
        super(TestRailCasesListener, self).__init__()

        self.testsuite_id = None
        # by default a TR Test Suites will be created if it does not exist
        self.create_testrail_testsuite = True

    def start_suite(self, name, attrs):
        if 's1' == attrs['id']:
            self.logger.open(self.logname)
            tr_section_id, msg = self.init_testrail_testsuite(name)
        else:
            tr_section_id, msg = self.init_testrail_section(name)
        self.logger.log(msg)
        self.suite_queue.push(name, tr_section_id)

    def start_test(self, name, attrs):
        # last ID appended is the TR Section ID for this RF test
        section_id = self.suite_queue.current_id()

        # ensure this RF test case does not already exist in TR
        try:
            cases = self.testrail.get_cases(self.project_id, self.testsuite_id, section_id)
        except TestRailAPIError as e:
            # log but do not quit.
            self.logger.log('{}.{}\n'.format(self.suite_queue.current_path(), name))
            self.logger.log('\tLISTENER ERROR: get test cases error: {}: {}\n'.format(e.code, e.error))
            return
        for c in cases:
            if name == c['title']:
                # it exists; do not create a new TR Case
                self.logger.log('{}.{}\n'.format(self.suite_queue.current_path(), name))
                return

        # create TR Case in current TR section
        try:
            resp = self.testrail.add_case(section_id, name, self.auto_type)
        except TestRailAPIError as e:
            # log but do not quit.
            self.logger.log('{}.{}\n'.format(self.suite_queue.current_path(), name))
            self.logger.log('\tLISTENER ERROR: add test case error: [{}: {}]\n'.format(e.code, e.error))
            return
        self.logger.log('{}.{} - created ({})\n'.format(self.suite_queue.current_path(), name, resp['id']))

    def end_test(self, name, attrs):
        # override base object behavior of logging test result
        pass

    def init_testrail_testsuite(self, rf_top_level_suite_name):
        # get TR Test Suite ID whose name matches RF suite name
        try:
            suites = self.testrail.get_suites(self.project_id)
        except TestRailAPIError as e:
            self.logger.log('LISTENER FATAL ERROR: get test suite error: {}: {}\n'.format(e.code, e.error), console=True)
            self.signal_quit()
        for s in suites:
            if rf_top_level_suite_name == s['name']:
                self.testsuite_id = s['id']

        # create TR Test Suite if allowed
        created = ''
        if self.testsuite_id is None:
            if not self.create_testrail_testsuite:
                # if not allowed to create TR Test Suite it must already exist
                self.logger.log('LISTENER FATAL ERROR: No ID for Testrail test suite\n', console=True)
                self.signal_quit()
            try:
                resp = self.testrail.add_suite(self.project_id, rf_top_level_suite_name)
            except TestRailAPIError as e:
                self.logger.log('LISTENER FATAL ERROR: add test suite error: {}: {}\n'.format(e.code, e.error), console=True)
                self.signal_quit()
            self.testsuite_id = resp['id']
            created = ' - created ({})'.format(self.testsuite_id)
        msg = 'Adding test Cases to Testrail from dry run of RF testsuite: {}\n\nSuites:\n{}{}\n'.format(
                rf_top_level_suite_name, rf_top_level_suite_name, created)
        return self.testsuite_id, msg

    def init_testrail_section(self, rf_suite_name):
        # last TR section ID pushed to suite queue is the parent of this RF suite name being processed.
        # but if that ID is also the testrail testsuite ID then this section has no parent id to be 
        # found or created under.
        cur_parent_id = self.suite_queue.current_id()
        if cur_parent_id == self.testsuite_id:
            cur_parent_id = None

        # get all sections in testsuite
        try:
            tr_sections = self.testrail.get_sections(self.project_id, self.testsuite_id)
        except TestRailAPIError as e:
            self.logger.log('LISTENER FATAL ERROR: get sections error: {}: {}\n'.format(e.code, e.error), console=True)
            self.signal_quit()

        # find current section ID if it exists ensuring parent_id is correct.
        # tr_section['parent_id'] will be None if this is a top-level TR section.
        # this is so sections with the same name but in different places do not get
        # used just becasue they were seen first.
        tr_section_id = None
        for tr_section in tr_sections:
            if rf_suite_name == tr_section['name'] and cur_parent_id == tr_section['parent_id']:
                tr_section_id = tr_section['id']

        # create TR section in TR Test Suite if not found
        created = ''
        if tr_section_id is None:
            try:
                resp = self.testrail.add_section(self.project_id, self.testsuite_id,
                        rf_suite_name, parent_id=cur_parent_id)
            except TestRailAPIError as e:
                self.logger.log('LISTENER FATAL ERROR: add section error: {}: {}\n'.format(e.code, e.error), console=True)
                self.signal_quit()
            tr_section_id = resp['id']
            created = ' - created ({})'.format(tr_section_id)
        return tr_section_id, '{}.{}{}\n'.format(self.suite_queue.current_path(), rf_suite_name, created)

