# Show all UIDs in Vault
import sys
import os
import getpass
import json
from datetime import datetime
from typing import Dict, Iterator, Tuple
# sys.path.append("..")  # pwd includes keepercommander"
#sys.path.append("../.venv/lib/python3.6/dist-packages")
from keepercommander import api, params # set PYTHONPATH=<absolute path to keepercommander>
from keepercommander.record import Record
from pprint import pprint

class KeeperSession(params.KeeperParams):
    ''' Login and sync_down automatically 
        user-ID is gotten from $KEEPER_USER
        user password if from $KEEPER_PASSWORD
        or parameters as with(user, password) '''
    USER = 'KEEPER_USER'
  
    # from keepercommander.api import login, sync_down
    
    def get_modified_timestamp(self, record_uid: str) -> float:
        current_rec = self.record_cache[record_uid]
        return current_rec['client_modified_time']
    
    def get_modified_datetime(self, record_uid):
        return datetime.fromtimestamp(self.get_modified_timestamp(record_uid) / 1000)

    def login(self, **kwargs):
        return api.login(self, **kwargs)
        
    def sync_down(self):
        return api.sync_down(self)
        
    def __enter__(self, user=None, password=None, user_prompt='User:', password_prompt='Password:'):
        _user = user or os.getenv(KeeperSession.USER) or input(user_prompt)
        _password = password or getpass.getpass(password_prompt)
        api.login(self, user=_user, password=_password)
        api.sync_down(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.clear_session()  # clear internal variables
    
    def get_every_unencrypted(self):
        for uid, packet in self.record_cache.items():
            yield uid, json.loads(packet['data_unencrypted'].decode('utf-8'))
 
    def get_every_record(self) -> Iterator[Tuple[str, Record]]:
        for uid in self.record_cache:
            rec = api.get_record(self, uid)       
            rec.timestamp = self.get_modified_timestamp(uid)
            rec.datetime = self.get_modified_datetime(uid)
            yield uid, rec
            
    def get_every_uid(self):
        for uid in self.record_cache:
            yield uid
            
    def get_all_uids(self):
        return self.record_cache.keys()
        
    def get_record_with_timestamp(self, uid: str) -> Dict[str, str]:
       '''timestamp is integer value of client_modified_time
       '''
       rec = api.get_record(self, uid).to_dictionary()    
       rec['timestamp'] = self.get_modified_timestamp(uid)
       return rec
       
    def get_record_with_datetime(self, uid: str) -> Dict[str, str]:
       rec = api.get_record(self, uid).to_dictionary()    
       rec['modified_time'] = datetime.fromtimestamp(self.get_modified_timestamp(uid))
       return rec
    
        

if __name__ == '__main__':
    import logging
    from operator import attrgetter
    logger = logging.getLogger(__file__)
    logger.setLevel(logging.INFO)
    inspects = [] # put UIDs to inspect as string literal like 'abc', comma separated 
    with KeeperSession() as keeper_login:
        uid_rec_dict = {u:r for (u, r) in keeper_login.get_every_record()}
        rec_list = uid_rec_dict.values() # [ keeper_login.get_record_with_datetime(uid) for uid in keeper_login.get_all_uids()]
        #for uid in keeper_login.get_all_uids():
        #    rec_list.append(keeper_login.get_record_with_timestamp(uid))
        sorted_list = sorted(rec_list, key=lambda r: r.timestamp, reverse=True) #   ['modified_time'
        for rr in sorted_list:
            dic = rr.to_dictionary()
            dic['modified_time'] = datetime.fromtimestamp(rr.timestamp / 1000)
            pprint(dic)
            #rr['modified_time'] = rr['modified_time'].isoformat()
            #print(json.dumps(rr, sort_keys=True, indent=4, ensure_ascii=False))
        
    exit(0)
