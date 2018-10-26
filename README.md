# Robotframework-Testrail-Listener
## Overview

A set of Robot Framework (**RF**) Listeners to add Cases and Results to Testrail (**TR**)

There are two RF Listeners which inherit from a base Listener:

1. **TestRailCasesListener.py**
  * Used to add Testrail Cases to Test Suites from a dryrun of robot on test data
2. **TestRailRunListener.py**
  * Use during normal robot test runs to add results to Testrail 

Milestones, Plans, Runs, Tests, and Results are added as tests are executed. The names 
of Milestones, Plans, and Runs are set by logic in the Listener.

The names of Testsuite Sections and Cases will be what RF determines.  In this way TestRail will reflect
the structure of your Robot Framework suites and the results will reflect how RF is run.

**TestRailListener.py** is the base class for the other two Listeners that do the work

**TestRailAPIClient.py** is the python bindings to Testrail API used by Listeners

## Install

1. Download or clone code where it can be placed in your python path
  * RF robot can be called with `--pythonpath [path to code]`
2. Copy site specific file **RENAME_TestRailServer.py** to **TestRailServer.py**
  * This file will contain your site specific settings.
  * By copying it future updates to Listener will not overwrite your settings.
3. Configure in **TestRailServer.py** function **get_testrail_srv_info()** with your TestRail server info
  * Review file for details on what changes are needed
4. Configure in **TestRailServer.py** function **set_testrail_name()** with your logic on how TestRail entities will be named for each test run
  * Review file for details on what changes are needed

It is recommended a temperory TestRail Project be created to test with.  This project can be delelted when ready
for production runs.  Note Project ID will need to be updated in TestRailServer.py.

## Operation

1. Run RF with TestRailCasesListener for each suite you want to support.
  * in example above this would be for API, GUI, and System

  `robot --listener TestRailCasesListener --dryrun system`

2. Run RF with TestRailRunListener for each model/run needed.

  `robot --listener TestRailRunListener system`

## Design Overview

During an RF run the TestRailRunListener will be called to update test results. Listener is designed so
TR Tests are created in a TR Run.  The Run will be created in a TR Plan.  One will be created if it does not exist.
The Plan is tied to a TR Milestone.  It also will be created if it does not exist.

The names used for the TestRail entities, Milestone, Plan, and Run are determined by the site specific logic 
configured in **TestRailServer.py**

An example usage would be the testing of a Release Canidate, e.g. FooBar 1.3 RC2, which would be the Milestone name.
For the testing cycle two models will be tested, Gizmo, and TNBT.  These would be the Plan names.  For each model 
each of the RF testsuites would be run, API, System, GUI.  These would be the Run names.

So TestRail will end up with these entities:

```
FooBar 1.3 RC2 (Milestone)
├── Gizmo (Plan)
│   ├── API (Run)
│   ├── GUI (Run)
│   └── System (Run)
└── TNBT (Plan)
    ├── API (Run)
    ├── GUI (Run)
    └── System (Run)
```

It does this by:

1. Create the Milestone and get its ID
2. Create the Plan for the model that is run first and get its ID
3. Create a Run in the Plan
4. As RF enters each new subsuite create a section in the Run and create all the Tests found
in the same section in the TR suite.
5. As each Test is completed update the Result in the Test.

On each future run, depending on how you setup the code, if a run uses an existing Milestone or Plan name, 
the Listener will use them.  The Run is created each time, even if it has the same name as an existing one.
This is allowed by TR since it uses unique IDs for all entities.

TestRailRunListener does not create Cases as it goes; it only creates Tests from existing Cases. If a Case is
missing the Listener will skip it and print a warning in the TR log it creates on each run.

To create the TR Cases the TestRailCasesListener is used.  A TR run is done with it using the 
--dryrun option (for speed) and it will create the Testsuite, Sections, and Cases as it traverses 
your RF suites.

The TestRailCasesListener can be run at any time.  It will ignore existing Cases and only create new ones.
Currently the design assumes the TR Project is configured to use multiple test suites to manage cases.  It will 
throw an error if this is not the case if a second test suite creation is attempted otherwise.

