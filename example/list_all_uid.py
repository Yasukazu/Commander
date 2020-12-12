# Show all UIDs and records in Vault
# set PYTHONPATH=<absolute path to keepercommander> AWS: /home/ec2-user/environment/Commander:/home/ec2-user/environment/.venv/lib/python3.6/dist-packages
import sys
import os
import getpass
import json
import datetime
import logging
import pylogrus
logging.setLoggerClass(pylogrus.PyLogrus)
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ycommander import params,api,record
from ycommander.error import AuthenticationError, NoUserExistsError

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

class WithParams(params.KeeperParams):
    ''' Login and sync_down automatically 
        user-ID is gotten from $KEEPER_USER
        user password if from $KEEPER_PASSWORD
        or parameters as with(user, password) '''
    USER = 'KEEPER_USER'
    PASSWORD = 'KEEPER_PASSWORD'
  
    
    def get_modified_timestamp(self, record_uid):
        current_rec = self.record_cache[record_uid]
        return current_rec['client_modified_time']
    
    def get_modified_time(self, record_uid):
        return datetime.datetime.fromtimestamp(self.get_modified_timestamp(record_uid) / 1000)

    def __enter__(self, user='', password='', user_prompt='Input User for KeeperParams:', password_prompt='Password:'):
        logger.info("Entering WithParams.")
        '''try:
            auth = self.pre_login()
        except AuthenticationError as err: '''
        if not self.auth_verifier:   
            self.user = self.user or user or os.getenv(WithParams.USER) or input(user_prompt)
            self.password = self.user or password or os.getenv(WithParams.PASSWORD) or getpass.getpass(password_prompt)
            auth = self.pre_login()

        api.login(self) # user=self.user, password=self.password)
        api.sync_down(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.clear_session()  # clear internal variables
    
    def get_every_unencrypted(self):
        for uid, packet in self.record_cache.items():
            yield uid, json.loads(packet['data_unencrypted'].decode('utf-8'))

            
    def get_all_uids(self):
        return self.record_cache.keys()
        
    import datetime
    def get_record(self, uid):
       dt = datetime.datetime.fromtimestamp(self.record_cache[uid]['client_modified_time'] / 1000)
       rec = api.get_record(self, uid)
       rec.modified_time = dt
       return rec

from operator import attrgetter

def list_all_uid():
    with WithParams() as keeper_session:
        rec_list = []
        for uid in keeper_session.get_all_uids():
            rec_list.append(keeper_session.get_record(uid))
        rec_list.sort(key=attrgetter('modified_time', 'title'))
        for rr in rec_list:
            rr_dict = rr.__dict__
            rr_dict['modified_time'] = rr.modified_time.isoformat()
            # rr_d = {k:v for k,v in rr_dict.items() if v is not None} # remove null value item
            print(json.dumps(rr_dict, sort_keys=True, indent=4, ensure_ascii=False))



if __name__ == '__main__':
    list_all_uid()
        