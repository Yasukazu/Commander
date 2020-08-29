# Session class for easy use of keepercommander
import sys
import os
import getpass
import json
import pprint
import zlib
from datetime import datetime
from typing import Dict, Iterator, Iterable, Tuple, Optional, Set, Generator, Union
from collections import defaultdict
from dataclasses import dataclass
from . import api, params # set PYTHONPATH=<absolute path to keepercommander>
from .record import Record
from .subfolder import get_folder_path, find_folders, BaseFolderNode
from .error import EmptyError
from .commands.folder import FolderMoveCommand
from .params import KeeperParams
from .tsrecord import Uid, Timestamp, TsRecord
import logging

logger = logging.getLogger(__file__)


class KeeperSession(params.KeeperParams):
    '''after login, sync_down
    context:
    '''

    def __init__(self, user: Optional[str]='', password: Optional[str]='', user_prompt: Optional[str]='Input Keeper session'):
        super().__init__()
        api.login(self, user=user, password=password)
        api.sync_down(self)
        self.g_record = api.get_record

    
    def get_modified_datetime(self, record_uid):
        return datetime.fromtimestamp(self.get_modified_timestamp(record_uid) / 1000)

    def login(self, **kwargs):
        return api.login(self, **kwargs)
        
    def sync_down(self):
        return api.sync_down(self)
        
    def __enter__(self): #, user: str='', password: str='', user_prompt='User:', password_prompt='Password:'):
        self.__deleted_uids: Set[Uid] = set()
        self.__to_delete_uids: Set[Uid] = set()
        self.update_records: Set[Uid] = set()
        self.__move_records: Dict[Uid, str] = {}
        self.__records: Dict[Uid, TsRecord] = {}
        self.__checksums: Dict[Uid, int] = {}
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if len(self.__to_delete_uids) > 0:
            delete_uids = (str(b) for b in self.__to_delete_uids)
            api.delete_records(self, delete_uids, sync=False)
            self.__deleted_uids |= self.__to_delete_uids
        if len(self.update_records) > 0:
            to_update_records = []
            for uid in self.update_records:
                r = self.get_record(uid)
                # if zlib.adler32(str(r).encode()) != self.__checksums[uid]:
                to_update_records.append(r)
            api.update_records(self, to_update_records, sync=False)
        if len(self.__move_records) > 0:
            move_cmd = FolderMoveCommand()
            for uid, dst in self.__move_records.items():
                resp = move_cmd.execute(self, src=uid, dst=dst)
                if resp and resp['result'] == 'success':
                    logger.info(f"{uid=} is moved to {dst=} from {uid=}.")
        # for i in self.update_records: api.update_record(self, self.update_records[i], sync=False)
        # self.clear_session()  # clear internal variables

    @property
    def to_move(self) -> Dict[Uid, str]:
        return self.__move_records

    def add_move(self, uid: Uid, dst: str):
        self.to_move[uid] = dst

    def uid_to_record(self, uid: Uid) -> Record:
        if uid not in self.__records:
            self.__records[uid] = self.get_record(uid)
        return self.__records[uid]

    @property
    def to_delete_uids(self) -> Set[Uid]:
        return self.__to_delete_uids

    def add_delete(self, uid: Uid):
        self.to_delete_uids.add(uid)

    def add_delete_set(self, uids: Set[Uid]):
        self.__to_delete_uids |= uids

    def add_update(self, uid: str):
        self.update_records.add(uid)

    def get_every_unencrypted(self):
        for uid, packet in self.record_cache.items():
            yield uid, json.loads(packet['data_unencrypted'].decode('utf-8'))

    def get_record(self, uuid: Uid) -> TsRecord:
        # caching by __records
        if uuid in self.__records:
            return self.__records[uuid]
        else:
            uid = str(uuid)
            rec = api.get_record(self, uid)
            # self.__checksums[uid] = zlib.adler32(str(rec).encode())
            ts = self.get_timestamp(uid)
            tsrec = TsRecord.new(rec, ts)
            # rec.datetime = self.get_modified_datetime(uid)
            self.__records[uuid] = tsrec
            return tsrec
    
    def get_every_record(self) -> Iterator[Tuple[Uid, TsRecord]]:
        for uid in self.record_cache:
            uuid = Uid(uid.encode('ascii'))
            yield uuid, self.get_record(uuid)
    
    def get_all_records(self) -> Dict[str, Record]:
        return {k: v for k, v in self.get_every_record()}
            
    def get_every_uid(self) -> Uid:
        for uid in self.record_cache:
            yield Uid(uid)
            
    def get_all_uids(self) -> Iterable[str]:
        return self.record_cache.keys()
        
    def get_record_with_timestamp(self, uid: Uid) -> Dict[str, str]:
       # timestamp is integer value of client_modified_time
       uid_s = uid.decode('ascii')
       rec = self.g_record(uid_s).to_dictionary()
       rec['timestamp'] = self.get_modified_timestamp(uid_s)
       return rec
       
    def get_record_with_datetime(self, uid: str) -> Dict[str, str]:
       rec = api.get_record(self, uid).to_dictionary()    
       rec['modified_time'] = datetime.fromtimestamp(self.get_modified_timestamp(uid))
       return rec
    
    def get_folders(self, record_uid: str) -> Optional[Iterable[str]]:
        return [get_folder_path(self, x) for x in find_folders(self, record_uid)]
    
    def find_duplicated(self) -> Iterator[Tuple[str, str, Dict[Timestamp, Set[Uid]]]]:
        # Checks 'login' and 'login_url' of Record.
        # Returns iterator of (login, login_node_url, {Timestamp: set(uid)}).
        for uid, rec in self.get_every_record():
            if not(rec.login and rec.login_node_url):
                continue
            same_dict = defaultdict(set) # Dict[str, Set[str]] {timestamp, set(uid,)} find same login and login_url
            same_dict[rec.timestamp].add(uid)
            for vid, rek in self.get_every_record():
                if vid == uid:
                    continue
                if rec.login == rek.login and rec.login_node_url == rek.login_node_url:
                    same_dict[rek.timestamp].add(vid)
            if sum(len(s) for s in same_dict.values()) > 1:
                yield rec.login, rec.login_node_url, same_dict

    def find_for_duplicated(self, user: str, netloc: str) -> Dict[str, Record]:
        # Find given 'login' and 'login_url' records.
        same_dict = {}
        for uid, rec in self.get_every_record():
            if rec.login == user and rec.login_node_url == netloc:
                same_dict[uid] = rec
        return same_dict

    def get_timestamp(self, record_uid: str) -> Timestamp:
      """get modified timestamp from cache in params
      might cause AttributeError or KeyError"""
      try:
        current_rec = self.record_cache[record_uid]
        ts = current_rec['client_modified_time']
      except KeyError as k:
          raise RecordError(f"No {k} key exists!") from KeyError
      except AttributeError as a:
          raise RecordError(f"No {a} attribute exists!") from AttributeError
      if not ts:
          raise RecordError(f"Client modified timestamp is null!")
      return Timestamp(ts)


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