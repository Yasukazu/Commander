# Session class for easy use of keepercommander
import sys
import os
import getpass
import json
import pprint
from datetime import datetime
from typing import Dict, Iterator, Iterable, Tuple, Optional, Set, Generator
from collections import defaultdict
from . import api, params # set PYTHONPATH=<absolute path to keepercommander>
from .record import Record
from .subfolder import get_folder_path, find_folders, BaseFolderNode

class KeeperSession(params.KeeperParams):
    ''' Login and sync_down automatically 
        user-ID is gotten from $KEEPER_USER
        user password if from $KEEPER_PASSWORD
        or parameters as with(user, password) '''
  
    def __init__(self, user: str='', password: str='', user_prompt='User:', password_prompt='Password:'):
        super().__init__(user=user or input(user_prompt),
         password=password or getpass.getpass(password_prompt))
        api.login(self)
        api.sync_down(self)

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
        self.delete_uids = set() # type: Set[str]
        self.update_records = {} # type: Dict[str, Record]
        self.all_records = {} # type: Dict[str, Record]
        for uid in self.record_cache:
            rec = api.get_record(self, uid)       
            rec.timestamp = self.get_modified_timestamp(uid)
            rec.datetime = self.get_modified_datetime(uid)
            self.all_records[uid] = rec
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if len(self.delete_uids) > 0:
            api.delete_records(self, self.delete_uids, sync=False)
        if len(self.update_records) > 0:
            api.update_records(self, self.update_records.values(), sync=False)
        # for i in self.update_records: api.update_record(self, self.update_records[i], sync=False)
        # self.clear_session()  # clear internal variables
    
    def add_delete(self, uid: str):
        self.delete_uids.add(uid)

    def add_update(self, r: Record):
        self.update_records[r.record_uid] = r

    def get_every_unencrypted(self):
        for uid, packet in self.record_cache.items():
            yield uid, json.loads(packet['data_unencrypted'].decode('utf-8'))
 
    def get_every_record(self) -> Iterator[Tuple[str, Record]]:
        for uid in self.all_records:
            yield uid, self.all_records[uid]
    
    def get_all_records(self) -> Dict[str, Record]:
        return self.all_records
            
    def get_every_uid(self) -> str:
        for uid in self.all_records:
            yield uid
            
    def get_all_uids(self) -> Iterable[str]:
        return self.all_records.keys()
        
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
    
    def get_folders(self, record_uid: str) -> Optional[Iterable[str]]:
        return [get_folder_path(self, x) for x in find_folders(self, record_uid)]
    
    def find_duplicated(self) -> Iterator[Dict[str, Set[str]]]:
        # uid_rec_dict = self.all_records # {u:r for (u, r) in self.get_every_record()}
        for uid, rec in self.all_records:
            same_dict = defaultdict(set) # Dict[str, Set[str]] {timestamp, set(uid,)} find same login and login_url
            for vid, rek in self.all_records.items():
                if vid == uid:
                    continue
                if (rec.login == rek.login and rec.login_url == rek.login_url):
                    # rec.login_url.split('?')[0] == rek.login_url.split('?')[0] # ignore parameter field of url
                    if len(same_dict) == 0:
                        same_dict[rec.timestamp].add(uid)
                    same_dict[rek.timestamp].add(vid)
            if len(same_dict):
                yield same_dict
                '''from_old_timestamp_list = sorted(same_dict.keys())
                for ts in from_old_timestamp_list[:-1]:
                    yield ts, same_dict[ts]
                '''

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