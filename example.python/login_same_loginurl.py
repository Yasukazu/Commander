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
from keepercommander.session import KeeperSession
from collections import defaultdict
import logging

logger = logging.getLogger(__file__)

def main(user: str, password: str, yesall: bool=False, repeat=0):
   # from operator import attrgetter
   # inspects = [] # put UIDs to inspect as string literal like 'abc', comma separated 
    with KeeperSession(user=user, password=password) as keeper_login:
        uid_rec_dict = {u:r for (u, r) in keeper_login.get_every_record()}
        # UPDATE_LIMIT = 2
        for uid, rec in uid_rec_dict.items():
            same_login_loginurl_set = defaultdict(set) # Dict[str, Set[str]] {timestamp, set(uid,)} find same login and login_url
            # same_login_loginurl_dict = {}
            for vid, rek in uid_rec_dict.items():
                if vid == uid:
                    continue
                if (rec.login == rek.login and
                    rec.login_url.split('?')[0] == rek.login_url.split('?')[0] and # ignore parameter field of url
                    ): # rec.timestamp != rek.timestamp):
                    if len(same_login_loginurl_set) == 0:
                        same_login_loginurl_set[rec.timestamp].add(uid)
                    same_login_loginurl_set[rek.timestamp].add(vid)
            # TODO: remove same timestamp
            if len(same_login_loginurl_set):
                from_old_timestamp_list = sorted(same_login_loginurl_set.keys())
                ts_delete_uid = {ts: same_login_loginurl_set[ts] for ts in from_old_timestamp_list[:-1]}
                logger.info(f"Dupricating records of older timestamp are going to be deleted: ")
                for uid_set in ts_delete_uid.values():
                    for uid in uid_set:
                        rec = uid_rec_dict[uid]
                        logger.info("\t" + pprint.pformat(rec))
                    keeper_login.delete_uids |= uid_set
                last_timestamp_uid_set = same_login_loginurl_set[from_old_timestamp_list[-1]]
                if len(last_timestamp_uid_set) > 1:
                    logger.info(f"last timestamp uid is duplicating: ")
                    for uid in last_timestamp_uid_set:
                        logger.info('\t' + uid)
                    
                repeat -= 0
                if not repeat:
                    break

                # timestamp_order_dict = {k: v for k, v in sorted(same_login_loginurl_set .items(), key=lambda item: item[1])}
                # for k in timestamp_order_dict:
                #   keeper_login.delete_records.add(k) # the smallest timestamp record
                #   update_count += 1
                #   if len(keeper_login.delete_records) >= UPDATE_LIMIT:
                #       return
                #   break

    exit(0)

if __name__ == '__main__':
    
    logger.setLevel(logging.INFO)
    api.logger.setLevel(logging.INFO)
    main(user=os.getenv('KEEPER_USER'), password=os.getenv('KEEPER_PASSWORD'), repeat=1)