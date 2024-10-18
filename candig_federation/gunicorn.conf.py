import os

bind = "0.0.0.0:4232"
workers = int(os.getenv("WORKERS", 4))
threads = int(os.getenv("THREADS", 4))
worker_class = "gevent"
user = "candig"
group = "candig"
loglevel = 'debug'
accesslog = '-'
access_log_format = 'INFO\t%(m)s\t%(U)s\t%(b)s\t%(M)s\t%(s)s'
capture_output = True
syslog = True