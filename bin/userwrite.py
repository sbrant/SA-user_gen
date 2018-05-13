#!/usr/bin/env python
# -----------------------------
# - Apply users from lookup to given servers
# -----------------------------

import csv
import sys
import random
import re
import json
import time
import os
from utils import parse
from splunklib.client import connect
from splunklib.searchcommands import dispatch, ReportingCommand, Configuration

splunkhome = os.environ['SPLUNK_HOME']

# create a KVStore collection so the lookup can be written
def createColl(comp):
    opts = parse(sys.argv[1:], {}, ".splunkrc")
    opts.kwargs["owner"] = "nobody"
    opts.kwargs["app"] = "SA-user_gen"
    service = connect(**opts.kwargs)


@Configuration()
class userGenCommand(ReportingCommand):
    @Configuration()
    def map(self, records):
        return records

    def reduce(self, records):
        for record in records:
            opts = parse(sys.argv[1:], {}, ".splunkrc")
            opts.kwargs["owner"] = "nobody"
            opts.kwargs["app"] = "SA-user_gen"
            service = connect(**opts.kwargs)
            collection = service.kvstore[kvs_coll]

if __name__ == "__main__":
   dispatch(userGenCommand, sys.argv, sys.stdin, sys.stdout, __name__)
