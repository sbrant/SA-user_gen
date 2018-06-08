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
import os
from utils import parse
from splunklib.client import connect
from splunklib.searchcommands import dispatch, ReportingCommand, Configuration
import csv

splunkhome = os.environ['SPLUNK_HOME']
thisapphome = os.path.join(splunkhome, "etc", "apps", "SA-user_gen")
lookupshome = os.path.join(thisapphome, "lookups")

def randomWords(num, dictionary=splunkhome+"/etc/apps/SA-user_gen/appserver/static/war"):
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
#    opts = parse(sys.argv[1:], {}, ".splunkrc")
#    opts.kwargs["owner"] = "nobody"
#    opts.kwargs["app"] = "SA-user_gen"
#    service = connect(**opts.kwargs)
#    service.kvstore.create(cname)
    return cname

def gameServers(users, version):
    if version == "botsv1":
        gs = (users / 8)+1
    elif version == "botsv2":
        gs = (users / 4)+1
    return gs

@Configuration()
class userGenCommand(ReportingCommand):
    @Configuration()
    def map(self, records):
        return records

    def reduce(self, records):
        for record in records:
            eventname = record['compname']
            kvs_coll = createColl(eventname)
            lookup_csv = open(os.path.join(lookupshome, kvs_coll + ".csv"), "w")
            fieldnames = ["password", "scoringurl", "gamingurl", "event", "username", "comptype", "gaming_servers"]
            csv_writer = csv.DictWriter(lookup_csv, fieldnames=fieldnames)
            csv_writer.writeheader()
            #opts = parse(sys.argv[1:], {}, ".splunkrc")
            #opts.kwargs["owner"] = "nobody"
            #opts.kwargs["app"] = "SA-user_gen"
            #service = connect(**opts.kwargs)
            #collection = service.kvstore[kvs_coll]
            contestants = int(record['contestants'])
            gservers = gameServers(contestants, record['comptype'])
            for user_entry in range(1, contestants+1):
                passwd = genPassword()
                tic = 1
                while tic <= gservers:
                    gurl = str(record['gaming'])
                    ftic = "{:0>2d}".format(tic)
                    fgurl = gurl.replace("XX",ftic)
                    collection_data = {"password": passwd,         \
                            "scoringurl": record['scoring'],       \
                            "gamingurl": fgurl,         \
                            "event": eventname,                    \
                            "username": 'user'+str(user_entry)+'-'+record['compname'], \
                            "comptype": record['comptype'], "gaming_servers": gservers}
                    tic+=1
                csv_writer.writerow(collection_data)
                #collection.data.insert(collection_data)
                yield {'password': passwd,                 \
                        'scoringurl': record['scoring'],   \
                        'gamingurl': fgurl,                \
                        'event': eventname,                \
                        'username': 'user'+str(user_entry)+'-'+record['compname']}
            lookup_csv.close()


if __name__ == "__main__":
   dispatch(userGenCommand, sys.argv, sys.stdin, sys.stdout, __name__)
