# Robotframework-Testrail-Listener
A set of Robot Framework Listeners to add Cases and Results to Testrail 

There are two RF Listeners which inherit from a base Listener:

1. TestRailCasesListener.py
  * Used to add Testrail Cases to Test Suites base on a dryrun of robot 
2. TestRailRunListener.py
  * Use during normal robot test runs to add to Testrail Milestones, Plans, and Runs with tests and add results as test execute.
