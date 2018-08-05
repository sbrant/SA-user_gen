import sys
import time
import requests
from splunklib.searchcommands import \
     dispatch, GeneratingCommand, Configuration, Option
import splunklib.client as client
import splunklib.results as results
import splunk.rest
import json
from urlparse import urlparse
import uuid
import re

@Configuration()
class MakeAccounts(GeneratingCommand):
    userlist = Option(require=True)
    username = Option(require=True)
    password = Option(require=True)
    role = Option(require=True)
    port = Option(require=True)
    action = Option(require=True)

    def generate(self):
        runid = uuid.uuid4().hex
        session_key = self._metadata.searchinfo.session_key

        # Retrieve the lookup
        kwargs_oneshot = {'count': 0}
        searchquery_oneshot = '|inputlookup {}'.format(self.userlist)        
        service = client.connect(host='127.0.0.1', port=8089, token=session_key)
        oneshotsearch_results = service.jobs.oneshot(searchquery_oneshot, **kwargs_oneshot)
        reader = results.ResultsReader(oneshotsearch_results)
        targets = set([])
        userpasswords = []
        for item in reader:
            scoringhost = urlparse(item['ScoringUrl']).hostname
            searchhost = urlparse(item['SearchUrl']).hostname
            targets.add(scoringhost)
            targets.add(searchhost)
            found = False
            for userpassword in userpasswords:
                if item['Username'] == userpassword['Username']:
                    found = True
            if not found:
                userpasswords.append({'Username': item['Username'], 'Password': item['Password']})
        
        target_tokens = []
        for target in targets:
            request = None
            try:
                request = requests.post('https://{}:{}/services/auth/login?output_mode=json'.format(target, self.port), verify = False, data = {'username' : self.username, 'password' : self.password})
                if request.status_code == 200:
                    target_session_key_dict = json.loads(request.text)
                    target_tokens.append({'target': target, 'session_key': target_session_key_dict['sessionKey']})
                    yield {'_time': time.time(), 'sourcetype': 'usergen:auth', 'source': runid, '_raw': 'Successful authentication to:{} as user:{}'.format(target, self.username) }
                else:
                    yield {'_time': time.time(), 'sourcetype': 'usergen:auth', 'source': runid, '_raw': 'Failed authentication to:{} as user:{}'.format(target, self.username) }
            except:
                yield {'_time': time.time(), 'sourcetype': 'usergen:auth', 'source': runid, '_raw': 'Failed connection to:{} as user:{}'.format(target, self.username) }

        for target in target_tokens:
            for user in userpasswords:
                try:
                    # First check if the user exists on the taget system
                    request = requests.get('https://{}:{}/services/authentication/users/{}'.format(target['target'], self.port,user['Username']), 
                                         headers={ 'Authorization': 'Splunk {}'.format(target['session_key'])}, 
                                         verify = False, 
                                         data = {'output_mode':'json'})

                    # If the user does not exist, and the action is create, attempt to create the user.
                    if self.action == 'create' and request.status_code == 404 and 'Could not find object id' in request.text:
                        request = requests.post('https://{}:{}/services/authentication/users'.format(target['target'], self.port), 
                                                headers={ 'Authorization': 'Splunk {}'.format(target['session_key'])}, 
                                                verify = False, 
                                                data = {'name': user['Username'] , 'password':user['Password'], 'roles':self.role, 'output_mode':'json'})
                        if request.status_code >= 200 and request.status_code <= 299:
                            yield {'_time': time.time(), 'sourcetype': 'usergen:create', 'source': runid, '_raw': 'User {} successfully created on {}. (HTTP status code {})'.format(user['Username'],target['target'], request.status_code) }
                        else:
                            yield {'_time': time.time(), 'sourcetype': 'usergen:create', 'source': runid, '_raw': 'User creation failed for {} on {}. (HTTP status code {})'.format(user['Username'],target['target'], request.status_code) }

                    # If the user exists and the action is delete, attempt to delete the user.
                    if self.action == 'delete' and request.status_code == 200:
                        request = requests.delete('https://{}:{}/services/authentication/users/{}'.format(target['target'], self.port,user['Username']), 
                                                headers={ 'Authorization': 'Splunk {}'.format(target['session_key'])}, 
                                                verify = False, 
                                                data = {'name': user['Username'] , 'output_mode':'json'})
                        if request.status_code >= 200 and request.status_code <= 299:
                            yield {'_time': time.time(), 'sourcetype': 'usergen:delete', 'source': runid, '_raw': 'User {} successfully deleted on {}. (HTTP status code {})'.format(user['Username'],target['target'], request.status_code) }
                        else:
                            yield {'_time': time.time(), 'sourcetype': 'usergen:create', 'source': runid, '_raw': 'User deletion failed for {} on {}. (HTTP status code {})'.format(user['Username'],target['target'], request.status_code) }

                except:
                    yield {'_time': time.time(), 'sourcetype': 'usergen:auth', 'source': runid, '_raw': 'Failed REST API to:{} as user:{}'.format(target['target'], self.username) }

dispatch(MakeAccounts, sys.argv, sys.stdin, sys.stdout, __name__)