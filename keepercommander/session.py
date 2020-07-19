# Session class for easy use of keepercommander
import sys
import os
import getpass
import json
import pprint
from datetime import datetime
from typing import Dict, Iterator, Tuple
from keepercommander import api, params # set PYTHONPATH=<absolute path to keepercommander>
from keepercommander.record import Record

class KeeperSession(params.KeeperParams):
    ''' Login and sync_down automatically 
        user-ID is gotten from $KEEPER_USER
        user password if from $KEEPER_PASSWORD
        or parameters as with(user, password) '''
  
    def __init__(self, user: str='', password: str='', user_prompt='User:', password_prompt='Password:'):
        super().__init__(user=user or input(user_prompt),
         password=password or getpass.getpass(password_prompt))

    def get_modified_timestamp(self, record_uid: str) -> float:
        current_rec = self.record_cache[record_uid]
        return current_rec['client_modified_time']
    
    def get_modified_datetime(self, record_uid):
        return datetime.fromtimestamp(self.get_modified_timestamp(record_uid) / 1000)

    def login(self, **kwargs):
        return api.login(self, **kwargs)
        
    def sync_down(self):
        return api.sync_down(self)
        
    def __enter__(self): #, user: str='', password: str='', user_prompt='User:', password_prompt='Password:'):
        api.login(self)
        api.sync_down(self)
        self.delete_records = set() # type: Set[str]
        self.update_records = {} # type: Dict[str, Record]
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if len(self.delete_records) > 0:
            api.delete_records(self, self.delete_records, sync=False)
        for i in self.update_records:
            api.update_record(self, self.update_records[i], sync=False)
        # self.clear_session()  # clear internal variables
    
    def add_delete(self, uid: str):
        self.delete_records.add(uid)

    def add_update(self, r: Record):
        self.update_records[r.record_uid] = r

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
    

def main(user='', password=''):
    from operator import attrgetter
    inspects = [] # put UIDs to inspect as string literal like 'abc', comma separated 
    with KeeperSession(user=user, password=password) as keeper_login:
        uid_rec_dict = {u:r for (u, r) in keeper_login.get_every_record() if r.totp}
        rec_list = uid_rec_dict.values() # [ keeper_login.get_record_with_datetime(uid) for uid in keeper_login.get_all_uids()]
        #for uid in keeper_login.get_all_uids():
        #    rec_list.append(keeper_login.get_record_with_timestamp(uid))
        sorted_list = sorted(rec_list, key=lambda r: r.timestamp, reverse=True) #   ['modified_time'
        for rr in sorted_list:
            dic = rr.to_dictionary()
            dic['modified_time'] = datetime.fromtimestamp(rr.timestamp / 1000).isoformat()
            dic['totp'] = rr.totp
            pprint(dic)
            #rr['modified_time'] = rr['modified_time'].isoformat()
            #print(json.dumps(rr, sort_keys=True, indent=4, ensure_ascii=False))
        
    exit(0)

if __name__ == '__main__':
    import logging
    
    logger = logging.getLogger(__file__)
    logger.setLevel(logging.INFO)
    main(user=os.getenv('KEEPER_USER'), password=os.getenv('KEEPER_PASSWORD'))