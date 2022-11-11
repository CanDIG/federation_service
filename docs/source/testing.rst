Testing the Federation Service
==============================


The Pytest library is used for automated testing of the Federation service and is divided into two test files.
The ``test_network.py`` set of tests are configuration related and check config validation regarding peer servers
and service json files. The bulk of the testing is done in ``test_uniform_federation.py``, which tests most
functions in both ``federation.py`` and ``operations.py``. Due to the nature of this service, being an aggregator
and communication tool between other services, many methods need to be mocked to simulate outgoing or incoming
messages from other services. 

Additionally, ``test_local_federation.py`` contains integration tests to check the expected output from unfederated and 
federated queries using real data instead of mocked responses. In order to run these, you need to run uwsgi instances in 
different ports following the instructions on the README. This simulates communication between two different servers. 
Finally, make sure you have access to the services specified in servers.json and that they are currently running. 
Since the Travis CI suite doesn't have access to the servers/services, these tests are skipped during CI when pushing 
changes to the repository.

If you are wanting to add more tests to the test suite, the ``test_structs.py`` found within ``tests/test_data``
contain a number of mocked classes to simulate responses along with data structures containing both input and 
output data.

The repo is hooked to Travis CI and will have all the tests run upon commit to any branch. If wanting to run the
tests locally, use the following command while in the main directory.

.. code-block:: bash

    $ pytest tests/

You may add ``-vv`` to the end for more verbose output, or use the following command to generate a readable html
of the test results:

.. code-block:: bash

    $ pytest --cov=candig_federation tests/ --html=test_report.html --self-contained-html