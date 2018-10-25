# Rename this file to TestRailServer.py and configure with correct TestRail server info
from robot.libraries.BuiltIn import BuiltIn


def get_testrail_srv_info():
    tr_srv = {}
    tr_srv['TESTRAIL_SERVER']     = 'testrail.example.com'
    tr_srv['TESTRAIL_PROTOCOL']   = 'http' # http or https
    tr_srv['TESTRAIL_PROJECT_ID'] = 1
    tr_srv['TESTRAIL_USER']       = 'buildmaster@example.com'
    tr_srv['TESTRAIL_PW']         = '12345678'
    return tr_srv


def set_testrail_names(logger):
    '''
    This function needs to be modified for each site the RF Listener is used with.

    It must return the names of TestRail entities use to store the current run's results
    in: Milestone, Plan, and Run.

    This run's result will be added to the Run given. This Run will be created in the Plan given.
    The Plan can already exist or it will be created. The Plan will be created or selected from
    the Milestone given. The Milestone will be created if it does not exist.

    logger is a handle to a log so this function can log info if desired.

    Code below is an example where info is obtained from Robot Framework's current run.
    In this case the run has made Device Under Test (DUT) API calls to get info on DUT
    such as model and firmware version
    '''
    # get info from RF to ID/create Testrail Milestone, test Plan, and test Run
    model        = BuiltIn().get_variable_value("$DUTMODEL")
    platform     = BuiltIn().get_variable_value("$DUTPLATFORM")
    fw_version   = BuiltIn().get_variable_value("$DUTVERSION")
    mac          = BuiltIn().get_variable_value("$DUTMAC")
    run_title    = BuiltIn().get_variable_value("$RUNTITLE")
    run_protocol = BuiltIn().get_variable_value("$HTTP ACCESS")

    # log what data is being used for this run
    site_specifc_info1 = ' - Model: {}\n - Platform: {}\n - Version: {}\n'.format(
            model, platform, fw_version)
    site_specifc_info2 = ' - MAC: {}\n - Title: {}\n - Protocol: {}\n'.format(
            mac, run_title, run_protocol)
    logger.log('{}{}'.format(site_specifc_info1, site_specifc_info2))

    # set names of Testrail entries used
    #
    # e.g Raven - 5.3.0-RC5
    milestone = '{} - {}'.format(platform, fw_version)
    # e.g RCX - Raven 5.3.0-RC5 [00:19:85:00:ad:20]
    plan      = '{} - {} {} [{}]'.format(model, platform, fw_version, mac)
    # e.g toucan (https) [RCX - Raven 5.3.0-RC5]
    run       = '{} ({}) [{} - {} {}]'.format(run_title, run_protocol, model, platform, fw_version)
    return milestone, plan, run
