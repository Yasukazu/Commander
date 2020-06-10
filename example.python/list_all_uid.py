# Show all UIDs in Vault
import sys
import os
import getpass
import json
import datetime

sys.path.append("..")  # pwd includes keepercommander"
#sys.path.append("../.venv/lib/python3.6/dist-packages")
from keepercommander import api, params # set PYTHONPATH=<absolute path to keepercommander>
from pprint import pprint

class WithParams(params.KeeperParams):
    ''' Login and sync_down automatically 
        user-ID is gotten from $KEEPER_USER
        user password if from $KEEPER_PASSWORD
        or parameters as with(user, password) '''
    USER = 'KEEPER_USER'
    PASSWORD = 'KEEPER_PASSWORD'
  
    # from keepercommander.api import login, sync_down
    
    def get_modified_timestamp(self, record_uid):
        current_rec = self.record_cache[record_uid]
        return current_rec['client_modified_time']
    
    def get_modified_time(self, record_uid):
        return datetime.datetime.fromtimestamp(self.get_modified_timestamp(record_uid) / 1000)

    def login(self, **kwargs):
        return api.login(self, **kwargs)
        
    def sync_down(self):
        return api.sync_down(self)
        
    def __enter__(self, user=None, password=None, user_prompt='User:', password_prompt='Password:'):
        self.user = user or os.getenv(WithParams.USER) or input(user_prompt)
        self.password = password or os.getenv(WithParams.PASSWORD) or getpass.getpass(password_prompt)
        api.login(self, user=self.user, password=self.password)
        api.sync_down(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.clear_session()  # clear internal variables
    
    def get_every_unencrypted(self):
        for uid, packet in self.record_cache.items():
            yield uid, json.loads(packet['data_unencrypted'].decode('utf-8'))
 
    def get_every_record(self):
        for uid in self.record_cache:
            yield uid, api.get_record(self, uid)       
            
    def get_every_uid(self):
        for uid in self.record_cache:
            yield uid
            
    def get_all_uids(self):
        return self.record_cache.keys()
        
    import datetime
    def get_record(self, uid):
       rec = api.get_record(self, uid).to_dictionary()    
       dt = datetime.datetime.fromtimestamp(self.record_cache[uid]['client_modified_time'] / 1000)
       rec['modified_time'] = dt
       return rec

        

if __name__ == '__main__':
    import logging
    from operator import attrgetter
    logger = logging.getLogger(__file__)
    logger.setLevel(logging.INFO)
    inspects = [] # put UIDs to inspect as string literal like 'abc', comma separated 
    with WithParams() as keeper_login:
        rec_list = []
        for uid in keeper_login.get_all_uids():
            rec_list.append(keeper_login.get_record(uid))
        sorted_list = sorted(rec_list, key=lambda r: r['modified_time'], reverse=True)    
        for rr in sorted_list:
            rr['modified_time'] = rr['modified_time'].isoformat()
            print(json.dumps(rr, sort_keys=True, indent=4, ensure_ascii=False))
        
    exit(0)
