Installation
============


After pulling the repo, create a virtual environment utilizing Python 3.7+ and install the requirements:

.. code-block:: bash

    $ pip install -r requirements.txt

After installation, the federation service should first be configured.


Configuration
-------------
There are three sections which need to be configured to properly set up the federation service.

1. The ``__main__.py`` file in ``federation_service/candig_federation``
2. The ``servers.json`` and ``services.json`` files in ``federation_service/configs``
3. The ``federation.ini`` configuration file for uWSGI


\__main__.py
^^^^^^^^^^^^

This file acts as the driver for the federation service as well as contains a number of default configuration settings.

.. code-block:: python

    parser.add_argument('--port', default=8890)
    parser.add_argument('--host', default='ga4ghdev01.bcgsc.ca')
    parser.add_argument('--logfile', default="./log/federation.log")
    parser.add_argument('--loglevel', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'])
    parser.add_argument('--services', default="./configs/services.json")
    parser.add_argument('--servers', default="./configs/servers.json")
    parser.add_argument('--schemas', default="./configs/schemas.json")

Any of these keyword arguments may be altered when running the service through the command line. Additional arguments
may be added by copying the format above.

============== ============
Argument        Explanation
-------------- ------------
``--port``      specifies the port the service should listen on.
``--host``      specifies the host address for the service.
``--logfile``   specifies the file which messages are logged to.
``--loglevel``  controls the verbosity of the logs.
``--services``  specifies a configuration file that tells Federation which services it should know about.
``--servers``     specifies a configuration file that tells Federation which peer servers it should know about.
============== ============



JSON configs
^^^^^^^^^^^^
Two types of configuration files are located in the ``configs`` folder, ``servers.json`` and ``services.json``, with examples for each marked by ``_ex``. 
Valid instances of both files are required in order to start the federation service. 

Each peer server is listed in a ``servers.json`` configuration file should correspond with the Tyk API Gateway for each CanDIG node,
including this node where federation service is running. In addition, specify the location for your peer servers with 
the array ``["research centre", "province name", "province code"]``. For compatibility with CanDIG's `data portal <https://github.com/CanDIG/candig-data-portal>`__, 
use the following province codes: 'ca-ab', 'ca-bc', 'ca-mb', 'ca-nb', 'ca-nl', 'ca-nt', 'ca-ns', 'ca-nu', 'ca-on', 'ca-pe', 'ca-qc', 'ca-sk', 'ca-yt'

For example, if your host federation service is running at ``http://0.0.0.0:8890`` in British Columbia, and your first 
peer server federation service is running at ``http://0.0.0.0:8891`` in Ontario, your ``servers.json``` would look like this:

.. code-block:: json

  {
    "servers": [
      {
        "url": "http://ga4ghdev01.bcgsc.ca:8891/federation/search",
        "location": [
          "BCGSC",
          "British Columbia",
          "ca-bc"
        ]
      },
      {
        "url": "http://ga4ghdev01.bcgsc.ca:8892/federation/search",
        "location": [
          "UHN",
          "Ontario",
          "ca-on"
        ]
      }
    ]
  }

In ``services.json``, each service should correspond to a CanDIG service accessible by the federation service. Due to the way request parsing works,
it's important to use the same service key name as its base API path.

.. code-block:: json

 {
   "services": {
        "katsu": "http://example1.com",
        "htsget": "http://example2.com"
   }
 }


uWSGI Configuration
^^^^^^^^^^^^^^^^^^^

The ``federation.ini`` file located in the top level of the directory controls uWSGI and should work as-is. The ``%d`` special variable indicates the directory containing this configuration file.

.. code-block:: ini

  [uwsgi]
  module = wsgi:application
  chdir = %d

  master = true
  processes = 3

  gid = candig
  socket = %d/federation.sock
  chmod-socket = 660
  vacuum = true

  die-on-term = true



