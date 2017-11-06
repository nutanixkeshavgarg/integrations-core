# (C) Datadog, Inc. 2010-2016
# All rights reserved
# Licensed under Simplified BSD License (see LICENSE)

# stdlib

# 3rd party
import requests

# project
from checks import AgentCheck

EVENT_TYPE = SOURCE_TYPE_NAME = 'squid'

METRIC_PREFIX = "squid"
SERVICE_CHECK = "squid.can_connect"
SQUID_COUNTERS = [
    "client_http.requests",
    "client_http.hits",
    "client_http.errors",
    "client_http.kbytes_in",
    "client_http.kbytes_out",
    "client_http.hit_kbytes_out",
    "server.all.requests",
    "server.all.errors",
    "server.all.kbytes_in",
    "server.all.kbytes_out",
    "server.http.requests",
    "server.http.errors",
    "server.http.kbytes_in",
    "server.http.kbytes_out",
    "server.ftp.requests",
    "server.ftp.errors",
    "server.ftp.kbytes_in",
    "server.ftp.kbytes_out",
    "server.other.requests",
    "server.other.errors",
    "server.other.kbytes_in",
    "server.other.kbytes_out",
    "icp.pkts_sent",
    "icp.pkts_recv",
    "icp.queries_sent",
    "icp.replies_sent",
    "icp.queries_recv",
    "icp.replies_recv",
    "icp.query_timeouts",
    "icp.replies_queued",
    "icp.kbytes_sent",
    "icp.kbytes_recv",
    "icp.q_kbytes_sent",
    "icp.r_kbytes_sent",
    "icp.q_kbytes_recv",
    "icp.r_kbytes_recv",
    "icp.times_used",
    "cd.times_used",
    "cd.msgs_sent",
    "cd.msgs_recv",
    "cd.memory",
    "cd.local_memory",
    "cd.kbytes_sent",
    "cd.kbytes_recv",
    "unlink.requests",
    "page_faults",
    "select_loops",
    "cpu_time",
    "swap.outs",
    "swap.ins",
    "swap.files_cleaned",
    "aborted_requests",
]

class SquidCheck(AgentCheck):

    def check(self, instance):

        name = instance.get("name")
        if not name:
            raise Exception("Each instance in squid.yaml must have a name")
        host = instance.get("host", "localhost")
        port = instance.get("port", 3128)
        cachemgr_passwd = instance.get("cachemgr_password", "")
        custom_tags = instance.get("tags", [])
        tags = ["name:%s" % name]

        # Get the squid counters values
        counters = self.get_counters(host, port, cachemgr_passwd, tags + custom_tags)

        # Send these values as rate
        for counter, value in counters.iteritems():
            self.rate(counter, value, tags=tags + custom_tags)

    def get_counters(self, host, port, pwd, tags):

        url = "http://%s:%s/squid-internal-mgr/counters" % (host, port)
        try:
            res = requests.get(url, auth=('datadog', pwd))
            res.raise_for_status()
            self.service_check(SERVICE_CHECK, AgentCheck.OK, tags=tags)
        except requests.exceptions.RequestException as e:
            self.service_check(SERVICE_CHECK, AgentCheck.CRITICAL, tags=tags)
            self.log.error('There was an error connecting to squid at %s: %s', url, e)
            raise

        # Each line is a counter in the form 'counter_name = value'
        raw_counters = res.text.split("\n")
        counters = {}
        for line in raw_counters:
            counter = line.strip().split(" = ")
            if counter[0] in SQUID_COUNTERS:
                counters["%s.%s" % (METRIC_PREFIX, counter[0])] = float(counter[1])

        return counters
