#!/usr/bin/env python

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
import math

splunkhome = os.environ['SPLUNK_HOME']
thisapphome = os.path.join(splunkhome, "etc", "apps", "SA-user_gen")
lookupshome = os.path.join(thisapphome, "lookups")
dictionary = "{}/bin/war".format(thisapphome)

def randomWords(num, words):
    chosen = []
    for i in range(num):
        chosen.append(random.choice(words))
    return(chosen)

def loadWords(dictionary):
    try:
        f = open(dictionary, "r")
    except (IOError):
        print "Cannot open dictionary file: {}".format(dictionary)
    words = []
    prog = re.compile("^[a-z]{4,8}$")  # reasonable length, no proper nouns
    for word in f:
        if(prog.match(word)):
            words.append(word.strip())
    return words

def genPassword(num, words):
    return("-".join(randomWords(num, words)))

@Configuration()
class userGenCommand(ReportingCommand):
    def map(self, records):
        return records
    
    def reduce(self, records):
        for record in records:
            if "pwlen" in record:
                pwlen = int(record['pwlen'])
            else:
                pwlen = 2

            if "numplayers" in record:
                numplayers = int(record['numplayers'])
            else:
                numplayers = 100

            if "eventname" in record:
                eventname = record['eventname']
            else:
                eventname = "default_event"

            if "scoringurl" in record:
                scoringurl = record['scoringurl']
            else:
                scoringurl = "None"

            if "searchurls" in record:
                searchurls_list = record['searchurls'].split(',')
                searchurls_list = [x.strip() for x in searchurls_list]
            else:
                searchurls_list = "None"

            errors=[]
            if pwlen < 1:
                errors.append( {
                    "Error" : "pwlen parameter must be an integer greater than 1"
                })

            if numplayers < 1:
                errors.append( {
                    "Error" : "numplayers parameter must be an integer greater than 1"
                })

            if "-" in eventname:
                errors.append( {
                    "Error" : "eventname cannot contain a '-' "
                })
            
            if errors:
                for error in errors:
                    yield(error)
                return
            
            words = loadWords(dictionary)
            width = int(math.log10(numplayers)) + 1
            numsearchurls = len(searchurls_list)
            for usernum in range(1, numplayers + 1):
                Password = genPassword(pwlen, words)
                record = {  
                    "DisplayUsername": "",
                    "Team": "",
                    "Password": Password, 
                    "Email": "",
                    "ScoringUrl": scoringurl, 
                    "SearchUrl": searchurls_list[(usernum % numsearchurls) - 1],                        
                    "Username": 'user{}-{}'.format(str(usernum).zfill(width), eventname), 
                    "Event": eventname
                }
                yield (record)

if __name__ == "__main__":
   dispatch(userGenCommand, sys.argv, sys.stdin, sys.stdout, __name__)