#!/usr/bin/env python
# -----------------------------
# - Generates random phrases for passwords
# - Generates user lookup for creating
# - Splunk users on BOTS systems
# -----------------------------

import csv
import sys
import random
import re
import json
import time
from utils import parse
from splunklib.client import connect
from splunklib.searchcommands import dispatch, ReportingCommand, Configuration

def randomWords(num, dictionary="/four/splunk/etc/apps/SA-ctf_scoreboard_admin/appserver/static/war"):
    r = random.SystemRandom()
    try:
        f = open(dictionary, "r")
    except (IOError):
        print "Need to have a valid hostname in the playbooks directory"
    count = 0
    chosen = []
    for i in range(num):
        chosen.append("")
    prog = re.compile("^[a-z]{4,8}$")  # reasonable length, no proper nouns
    if(f):
        for word in f:
            if(prog.match(word)):
                for i in range(num):
                    if(r.randint(0, count) == 0):
                        chosen[i] = word.strip()
                        count += 33
    return(chosen)

def genPassword(num=2):
    return("-".join(randomWords(num)))

# create a KVStore collection so the lookup can be written
def createColl(comp):
    etime = str(int(time.time()))
    cname = comp+'-'+etime
    opts = parse(sys.argv[1:], {}, ".splunkrc")
    opts.kwargs["owner"] = "nobody"
    opts.kwargs["app"] = "SA-Usergen"
    service = connect(**opts.kwargs)
    service.kvstore.create(cname)


@Configuration()
class userGenCommand(ReportingCommand):
    @Configuration()
    def map(self, records):
        return records

    def reduce(self, records):
        for record in records:
            eventname = record['compname']
            createColl(eventname)
            # write relevant fields, from each record, to KVStore
            for user_entry in range(1, int(record['contestants'])+1):
                yield {'password': genPassword(), 'scoringurl': record['scoring'], 'gamingurl': record['gaming'], 'event': eventname, 'username': 'user'+str(user_entry)+'-'+record['compname']}
            # return the contents lookup

if __name__ == "__main__":
   dispatch(userGenCommand, sys.argv, sys.stdin, sys.stdout, __name__)
