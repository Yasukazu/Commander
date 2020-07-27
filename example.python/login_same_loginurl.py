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

def main(user: str, password: str, yesall: bool=False):
   # from operator import attrgetter
   # inspects = [] # put UIDs to inspect as string literal like 'abc', comma separated 
    with KeeperSession(user=user, password=password) as keeper_login:
        uid_rec_dict = {u:r for (u, r) in keeper_login.get_every_record()}
        UPDATE_LIMIT = 2
        for uid, rec in uid_rec_dict.items():
            same_login_loginurl_set = {} # find same login and login_url
            # same_login_loginurl_dict = {}
            for vid, rek in uid_rec_dict.items():
                if vid == uid:
                    continue
                if rec.login == rek.login and rec.login_url == rek.login_url and rec.timestamp != rek.timestamp:
                    if len(same_login_loginurl_set):
                        same_login_loginurl_set[vid] = rek.timestamp
                    else:
                        same_login_loginurl_set[vid] = rek.timestamp
                        same_login_loginurl_set[uid] = rec.timestamp
                        # (uid,vid) if uid < vid else (vid,uid))
                    # same_login_loginurl_dict[uid] = rec
                    # same_login_loginurl_dict[vid] = rek
            # TODO: remove same timestamp
            if len(same_login_loginurl_set):
                timestamp_order_dict = {k: v for k, v in sorted(same_login_loginurl_set
                 .items(), key=lambda item: item[1])}
                for k in timestamp_order_dict:
                    keeper_login.delete_records.add(k) # the smallest timestamp record
                    update_count += 1
                    if len(keeper_login.delete_records) >= UPDATE_LIMIT:
                        return
                    break

    exit(0)

if __name__ == '__main__':
    
    logger.setLevel(logging.INFO)
    api.logger.setLevel(logging.INFO)
    main(user=os.getenv('KEEPER_USER'), password=os.getenv('KEEPER_PASSWORD'), yesall=True)