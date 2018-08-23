#
# TestRail API binding for Python 2.x (API v2, available since
# TestRail 3.0)
#
# Learn more:
#
# http://docs.gurock.com/testrail-api2/start
# http://docs.gurock.com/testrail-api2/accessing
#
import urllib2, json, base64


class TestRailAPIClient:


    def __init__(self, server, protocol='http', user=None, password=None):
        self.user = user
        self.password = password
        self.__url = '{}://{}/{}'.format(protocol, server, 'index.php?/api/v2/')

    def send_get(self, uri):
        '''

         Send Get

         Issues a GET request (read) against the API and returns the result
         (as Python dict).

         Arguments:

         uri                 The API method to call including parameters
                             (e.g. get_case/1)

         '''
        return self.__send_request('GET', uri, None)

    def send_post(self, uri, data={}):
        '''

        Send POST

        Issues a POST request (write) against the API and returns the result
        (as Python dict).

        Arguments:

        uri                 The API method to call including parameters
                            (e.g. add_case/1)
        data                The data to submit as part of the request (as
                            Python dict, strings must be UTF-8 encoded)
        '''
        return self.__send_request('POST', uri, data)

    def __send_request(self, method, uri, data):
        url = self.__url + uri
        request = urllib2.Request(url)
        if method == 'POST':
            request.add_data(json.dumps(data))
        auth = base64.b64encode('{}:{}'.format(self.user, self.password))
        request.add_header('Authorization', 'Basic {}'.format(auth))
        request.add_header('Content-Type', 'application/json')

        e = None
        try:
            response = urllib2.urlopen(request).read()
        except urllib2.HTTPError as e:
            response = e.read()

        if response:
            result = json.loads(response)
        else:
            result = {}

        if e is not None:
            if result and 'error' in result:
                # testrail specific exception
                raise TestRailAPIError(e.code, result['error'])
            else:
                # raise last exception
                raise
        return result

    def get_projects(self):
        uri = 'get_projects'
        return self.send_get(uri)

    def get_project(self, project_id):
        uri = 'get_project/{}'.format(project_id)
        return self.send_get(uri)

    def get_milestones(self, project_id):
        uri = 'get_milestones/{}'.format(project_id)
        return self.send_get(uri)

    def get_milestone(self, milestone_id):
        uri = 'get_milestone/{}'.format(milestone_id)
        return self.send_get(uri)

    def add_milestone(self, project_id, name, description=None):
        uri = 'add_milestone/{}'.format(project_id)
        data = {'name': name}
        if description is not None:
            data['description'] = description
        return self.send_post(uri, data)

    def close_milestone(self, milestone_id):
        uri = 'update_milestone/{}'.format(milestone_id)
        data = {'is_completed': True}
        return self.send_post(uri, data)

    def delete_milestone(self, milestone_id):
        uri = 'delete_milestone/{}'.format(milestone_id)
        return self.send_post(uri)

    def get_plans(self, project_id, milestone_id=None):
        uri = 'get_plans/{}'.format(project_id)
        if milestone_id is not None:
            uri = '{}&milestone_id={}'.format(uri, milestone_id)
        return self.send_get(uri)

    def get_plan(self, plan_id):
        uri = 'get_plan/{}'.format(plan_id)
        return self.send_get(uri)

    def add_plan(self, project_id, name, description=None, milestone_id=None):
        uri = 'add_plan/{}'.format(project_id)
        data = {'name': name}
        if description is not None:
            data['description'] = description
        if milestone_id is not None:
            data['milestone_id'] = milestone_id
        return self.send_post(uri, data)

    def add_plan_entry(self, plan_id, suite_id, name, case_ids=None, include_all=None, description=None, assignedto_id=None):
        uri = 'add_plan_entry/{}'.format(plan_id)
        if include_all is not None:
            if include_all and case_ids:
                raise TestRailAPIError(99, 'Test run requested to include all but has custom case IDs')
        data = {'name': name, 'suite_id': suite_id}
        if include_all is not None:
            data['include_all'] = include_all
        if case_ids is not None:
            data['case_ids'] = case_ids
        if description is not None:
            data['description'] = description
        if assignedto_id is not None:
            data['assignedto_id'] = assignedto_id
        return self.send_post(uri, data)

    def update_plan(self, plan_id, name=None, description=None, milestone_id=None):
        uri = 'update_plan/{}'.format(plan_id)
        data = {}
        if name is not None:
            data['name'] = name
        if description is not None:
            data['description'] = description
        if milestone_id is not None:
            data['milestone_id'] = milestone_id
        return self.send_post(uri, data)

    def update_plan_entry(self, plan_id, entry_id, name=None, case_ids=None, run_id=None, include_all=None, description=None, assignedto_id=None):
        uri = 'update_plan_entry/{}/{}'.format(plan_id, entry_id)
        if include_all is not None:
            if include_all and case_ids:
                raise TestRailAPIError(99, 'Test run requested to include all but has custom case IDs')
        data = {}
        if name is not None:
            data['name'] = name
        if include_all is not None:
            data['include_all'] = include_all
        if description is not None:
            data['description'] = description
        if assignedto_id is not None:
            data['assignedto_id'] = assignedto_id
        if case_ids is not None:
            data['case_ids'] = list(case_ids)
            if run_id is not None:
                # special behavior:
                # perform update by adding case_ids to existing
                # ones in the given run of this entry.
                existing_tests = self.get_tests(run_id)
                for t in existing_tests:
                    data['case_ids'].append(t['case_id'])
        return self.send_post(uri, data)

    def close_plan(self, plan_id):
        uri = 'close_plan/{}'.format(plan_id)
        return self.send_post(uri)

    def delete_plan(self, plan_id):
        uri = 'delete_plan/{}'.format(plan_id)
        return self.send_post(uri)

    def get_run(self, run_id):
        uri = 'get_run/{}'.format(run_id)
        return self.send_get(uri)

    def close_run(self, run_id):
        uri = 'close_run/{}'.format(run_id)
        return self.send_post(uri)

    def delete_run(self, run_id):
        uri = 'delete_run/{}'.format(run_id)
        return self.send_post(uri)

    def get_tests(self, run_id):
        uri = 'get_tests/{}'.format(run_id)
        return self.send_get(uri)

    def get_test(self, test_id):
        uri = 'get_test/{}'.format(test_id)
        return self.send_get(uri)

    def add_result(self, test_id, result_id, elapsed=None, comment=None, version=None, defects=None):
        uri = 'add_result/{}'.format(test_id)
        data = {'status_id': result_id}
        if elapsed is not None:
            data['elapsed'] = elapsed
        if comment is not None:
            data['comment'] = comment
        if version is not None:
            data['version'] = version
        if defects is not None:
            data['defects'] = defects
        return self.send_post(uri, data)

    def add_result_for_case(self, run_id, case_id, result_id, elapsed=None, comment=None, version=None, defects=None):
        uri = 'add_result_for_case/{}/{}'.format(run_id, case_id)
        data = {'status_id': result_id}
        if elapsed is not None:
            data['elapsed'] = elapsed
        if comment is not None:
            data['comment'] = comment
        if version is not None:
            data['version'] = version
        if defects is not None:
            data['defects'] = defects
        return self.send_post(uri, data)

    def get_suites(self, project_id):
        uri = 'get_suites/{}'.format(project_id)
        return self.send_get(uri)

    def get_suite(self, suite_id):
        uri = 'get_suite/{}'.format(suite_id)
        return self.send_get(uri)

    def add_suite(self, project_id, name, description=None):
        uri = 'add_suite/{}'.format(project_id)
        data = {'name': name}
        if description:
            data['description'] = description
        return self.send_post(uri, data)

    def get_sections(self, project_id, suite_id):
        uri = 'get_sections/{}&suite_id={}'.format(project_id, suite_id)
        return self.send_get(uri)

    def get_section(self, suite_id):
        uri = 'get_section/{}'.format(suite_id)
        return self.send_get(uri)

    def add_section(self, project_id, suite_id, name, parent_id=None, description=None):
        uri = 'add_section/{}'.format(project_id)
        data = {'name': name, 'suite_id': suite_id}
        if parent_id:
            data['parent_id'] = parent_id
        if description:
            data['description'] = description
        return self.send_post(uri, data)

    def get_automated_test_case_type(self):
        uri = 'get_case_types'
        response = self.send_get(uri)
        for tc_type in response:
            if 'Automated' == tc_type['name']:
                return tc_type['id']
        raise TestRailAPIError(99, "'Automated' testcase type not found'")

    def get_cases(self, project_id, suite_id, section_id=None):
        uri = 'get_cases/{}&suite_id={}'.format(project_id, suite_id)
        if section_id:
            uri = '{}&section_id={}'.format(uri, section_id)
        return self.send_get(uri)

    def add_case(self, section_id, title, type_id):
        uri = 'add_case/{}'.format(section_id)
        data = {'title': title, 'type_id': type_id}
        return self.send_post(uri, data)

    def get_user_id(self, user):
        uri = 'get_users'
        users = self.send_get(uri)
        for u in users:
            if user == u['name'] or user == u['email']:
                return u['id']
        raise TestRailAPIError(99, '[{}] not found'.format(user))


class TestRailAPIError(Exception):


    def __init__(self, code, error):
        self.code = code
        self.error = error

