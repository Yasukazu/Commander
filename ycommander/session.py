# Session class for easy use of ycommander
import os
import sys
import json
import pprint
from argparse import ArgumentParser
from datetime import datetime
from typing import Dict, Iterator, Iterable, Tuple, Optional, Set, List, Generator, Union
from collections import defaultdict, namedtuple
import unicodedata
from . import api
from .configarg import PARSER as main_parser  # set PYTHONPATH=<absolute path to ycommander>
from . params import KeeperParams
from .record import Record
from .subfolder import get_folder_path, find_folders, BaseFolderNode
from .commands.folder import FolderMoveCommand
from .tsrecord import Uid, Timestamp, TsRecord
from .error import RecordError

# from functools import cached_property
import logging
logger = logging.getLogger(__name__)

PARSER = main_parser

class KeeperSession:
    '''after login, sync_down
    context:
    '''


    @staticmethod
    def options() -> str:
        return main_parser.format_usage()

    def __init__(self, params: KeeperParams = None,
                 user: str = '', password: str = '', user_prompt: str = 'Input Keeper user:',
                 settings: Optional[List[str]] = None, sync_down=True):
        if params:
            self.params = params
        else:
            if settings is None:
                settings = sys.argv
            from .configarg import configure
            self.params, opts, flags = configure(settings)
            self.__session_token = api.login(self.params, user=user, user_prompt=user_prompt)
        self.__record_cache = self.sync_down() if sync_down else None
        self.__uids: Set[Uid] = {Uid.new(uid) for uid in self.__record_cache.keys()} if self.__record_cache else None
        self.__records: Dict[Uid, TsRecord] = {}
        self.__deleted_uids: Set[Uid] = set()
        self.__to_delete_uids: Set[Uid] = set()
        self.update_records: Set[Uid] = set()
        self.__move_records: Dict[Uid, str] = {}
        self._get_record = api.get_record
        self._delete_records = api.delete_records

    def get_modified_datetime(self, record_uid):
        return datetime.fromtimestamp(self.params.get_modified_timestamp(record_uid) / 1000)

    def login(self, **kwargs):
        return api.login(self.params, **kwargs)
        
    def sync_down(self) -> Dict[str, bytes]:
        logger.info('Sync_down starts..')
        r = api.sync_down(self.params)
        logger.info('..done sync_down.')
        return r

    def __getitem__(self, uid: Uid) -> TsRecord:
        '''[paren] access
        '''
        return self.record_at(uid)

    def __enter__(self): #, user: str='', password: str='', user_prompt='User:', password_prompt='Password:'):
        # self.__revisions: Dict[Uid, int] = {Uid(uid):}
        self.__checksums: Dict[Uid, int] = {}
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if len(self.__to_delete_uids) > 0:
            delete_uids = (str(b) for b in self.__to_delete_uids)
            api.delete_records(self.params, delete_uids, sync=False)
            self.__deleted_uids |= self.__to_delete_uids
        if len(self.update_records) > 0:
            to_update_records = []
            for uid in self.update_records:
                r = self.record_at(uid)
                # if zlib.adler32(str(r).encode()) != self.__checksums[uid]:
                to_update_records.append(r)
            api.update_records(self.params, to_update_records, sync=False)
        if len(self.__move_records) > 0:
            move_cmd = FolderMoveCommand()
            for uid, dst in self.__move_records.items():
                resp = move_cmd.execute(self.params, src=uid, dst=dst)
                if resp:
                    logger.info(f"'uid'({uid}) is moved to 'dst'({dst}) from 'uid'({uid}) with revision {resp}.")
        # for i in self.update_records: api.update_record(self, self.update_records[i], sync=False)
        # self.clear_session()  # clear internal variables

    @property
    def to_move(self) -> Dict[Uid, str]:
        return self.__move_records

    def add_move(self, uid: Uid, dst: str):
        self.to_move[uid] = dst

    def move_immediately(self, uid: Uid, dst: str) -> Optional[int]:
        move_cmd = FolderMoveCommand()
        resp = move_cmd.execute(self.params, src=str(uid), dst=dst)
        if not resp:
            logger.exception(f"Failed to move folder of 'uid'({uid}) to 'dst'({dst}).")
            return
        self.__records[uid].folder = dst
        self.__records[uid].revision = resp
        return resp

    def uid_to_record(self, uid: Uid) -> Record:
        if uid not in self.__records:
            self.__records[uid] = self.record_at(uid)
        return self.__records[uid]

    @property
    def to_delete_uids(self) -> Set[Uid]:
        return self.__to_delete_uids

    def add_delete(self, uid: Uid):
        self.to_delete_uids.add(uid)

    def add_delete_set(self, uids: Set[Uid]):
        self.__to_delete_uids |= uids

    def delete_immediately(self, uids: Iterable[Union[Uid, str]]):
        uid = None
        for uid in uids:
            break
        if not uid:
            return
        if isinstance(uid, str):
            uids = set([Uid.new(uid) for uid in uids])
        elif isinstance(uid, Uid):
            uids = set(uids)
        else:
            return
        uids -= self.__deleted_uids
        assert uids <= self.__uids  # set([uid for uid in uids if uid in self.__uids])
        delete_uids = [str(b) for b in uids]
        api.delete_records(self.params, delete_uids, sync=False)
        self.__uids -= uids
        self.__deleted_uids |= uids

    def add_update(self, uid: str):
        self.update_records.add(uid)

    def get_every_unencrypted(self):
        for uid, packet in self.params.record_cache.items():
            yield uid, json.loads(packet['data_unencrypted'].decode('utf-8'))

    def record_at(self, uuid: Uid) -> TsRecord:
        ''' caching by __records
        @param uuid:
        @return:
        '''
        if uuid not in self.__uids:
            raise KeyError(f"'str(uuid)'({str(uuid)}) not in self.__uids")
        if uuid in self.__records:
            return self.__records[uuid]
        else:
            uid = str(uuid)
            rec = api.get_record(self.params, uid)
            # self.__checksums[uid] = zlib.adler32(str(rec).encode())
            ts = self.get_timestamp(uid)
            tsrec = TsRecord.new(rec, ts)
            # rec.datetime = self.get_modified_datetime(uid)
            self.__records[uuid] = tsrec
            return tsrec
    
    def get_every_record(self) -> Iterator[Tuple[Uid, TsRecord]]:
        for uid in self.__uids:
            yield uid, self.record_at(uid)
    
    def get_all_records(self) -> Dict[Uid, TsRecord]:
        return {k: v for k, v in self.get_every_record()}
            
    def get_every_uid(self) -> Uid:
        for uid in self.__uids:
            yield uid
            
    def get_all_uids(self) -> Set[Uid]:
        '''

        @return: copy of __uids
        '''
        return self.__uids.copy()
        
    def get_record_with_timestamp(self, uid: Uid) -> Dict[str, str]:
        # timestamp is integer value of client_modified_time
        rec = self._get_record(self.params, str(uid)).to_dictionary()
        rec['timestamp'] = self.params.get_modified_timestamp(uid)
        return rec
       
    def get_record_with_datetime(self, uid: str) -> Dict[str, str]:
        rec = api.get_record(self.params, uid).to_dictionary()
        rec['modified_time'] = datetime.fromtimestamp(self.params.get_modified_timestamp(uid) / 1000)
        return rec
    
    def get_folders(self, record_uid: str) -> Optional[Iterable[str]]:
        return [get_folder_path(self, x) for x in find_folders(self, record_uid)]

    def find_duplicating_username_url(self):
        records: List[TsRecord] = [r for r in self.get_all_records().values()]

        def get_user_location(record: TsRecord):
            ex_ch_grp = '\x03\x10'  # Keeper inserts '\x10' into empty fields sometimes...
            return record.username.strip(ex_ch_grp), record.url.strip(ex_ch_grp)
        records.sort(key=get_user_location)
        from itertools import groupby
        for k, g in groupby(records, get_user_location):
            group_list = list(g)
            if k[0] and k[1] and len(group_list) > 1:
                yield k, group_list

    def find_duplicated(self) -> Iterator[Tuple[str, str, Dict[Timestamp, Set[Uid]]]]:
        # Checks 'login' and 'login_url' of Record.
        # Returns iterator of (login, login_node_url, {Timestamp: set(uid)}).
        yielded_username_url_set: Set[Tuple[str, str]] = set()
        for uid in self.get_all_uids():
            try:
                rec = self.record_at(uid)
            except KeyError:
                continue
            if (not(rec.username and rec.login_node_url) or
                    (rec.username, rec.login_node_url) in yielded_username_url_set):
                continue
            same_dict = defaultdict(set)  # Dict[str, Set[str]] {timestamp, set(uid,)} find same login and login_url
            same_dict[rec.timestamp].add(uid)
            found = False
            for vid in self.get_all_uids().copy():
                if vid == uid:
                    continue
                try:
                    rek = self.record_at(vid)
                except KeyError:
                    continue
                if (rec.username == rek.username and
                        rec.login_node_url == rek.login_node_url):
                    same_dict[rek.timestamp].add(vid)
                    found = True
            if found:  # sum(len(s) for s in same_dict.values()) > 1:
                yield rec.username, rec.login_node_url, same_dict
                yielded_username_url_set.add((rec.username, rec.login_node_url))

    def find_for_duplicated(self, user: str, netloc: str) -> Dict[Uid, Record]:
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
            current_rec = self.params.record_cache[record_uid]
            ts = current_rec['client_modified_time']
        except KeyError as k:
            raise RecordError(f"No {k} key exists!") from KeyError
        except AttributeError as a:
            raise RecordError(f"No {a} attribute exists!") from AttributeError
        if not ts:
            raise RecordError(f"Client modified timestamp is null!")
        return Timestamp(ts)


def main(user='', password=''):
    # from operator import attrgetter
    # inspects = []  # put UIDs to inspect as string literal like 'abc', comma separated
    with KeeperSession(user=user, password=password) as keeper_login:
        uid_rec_dict = {u:r for (u, r) in keeper_login.get_every_record() if r.totp}
        rec_list = uid_rec_dict.values()
        sorted_list = sorted(rec_list, key=lambda r: r.timestamp, reverse=True) #   ['modified_time'
        for rr in sorted_list:
            dic = rr.to_dictionary()
            dic['modified_time'] = datetime.fromtimestamp(rr.timestamp / 1000).isoformat()
            dic['totp'] = rr.totp
            pprint.pprint(dic)

    exit(0)


if __name__ == '__main__':
    from loguru import logger  # logger = logging.getLogger(__file__)
    # logger.setLevel(logging.INFO)
    main(user=os.getenv('KEEPER_USER'), password=os.getenv('KEEPER_PASSWORD'))