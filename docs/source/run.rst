Starting Federation
===================
There are two options for running the Federation service.

.. code-block:: bash

    $ python -m candig_federation

This runs the Flask application directly and offers the ability to change the application configuration through keyword
arguments. With nothing specified, the defaults listed in __main__ of ``candig_federation`` will be used.
.. note::

    The above method is useful for spawning local Federation nodes for simulating more CanDIG sites, but any instance spawned may **not** be used
    as the initial node receiving the request. An instance spawned utilizing uWSGI is required to handle response aggregation. See
    `request flow`__ for a better explanation.

.. code-block:: bash

    $ uwsgi federation.ini --http <host>:<port>

This command utilizes uWSGI to run the service as is controlled through the `federation.ini` configuration file. For request aggregation
to function, uWSGI needs to be started with at least two processes.


