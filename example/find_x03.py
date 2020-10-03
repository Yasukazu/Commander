# Session class for easy use of ycommander
import sys
import os
import getpass
import json
import pprint
from datetime import datetime
from typing import Dict, Iterator, Tuple
from ycommander import api, params # set PYTHONPATH=<absolute path to ycommander>
from ycommander.record import Record
from ycommander.session import KeeperSession
from collections import defaultdict
import logging

logger = logging.getLogger(__file__)

INVALID_URL = 'http://sn'
CNTRL_CODE = '\x10' # data link escape (+)

def main(user: str, password: str, yesall: bool=False):
   # from operator import attrgetter
   # inspects = [] # put UIDs to inspect as string literal like 'abc', comma separated 
    with KeeperSession(user=user, password=password) as keeper_login:
        uid_rec_dict = {u:r for (u, r) in keeper_login.get_every_record()}
        update_count = 0
        UPDATE_LIMIT = 2
        for uid, rec in uid_rec_dict.items():
            if CNTRL_CODE in (rec.title, rec.login, rec.login_url, rec.password, rec.notes):
                print(f"Record {rec.record_uid}(Title: {rec.title}) has a Control-code name (Title, Login_id, Login_url, password, notes): {rec}")
                # find same login and login_url
                # same_login_loginurl = {}
                for vid, rek in uid_rec_dict.items():
                    if rec.login == rek.login and rec.login_url == rek.login_url:
                        # same_login_loginurl[vid] = rek
                        if CNTRL_CODE in rek.title: rek.title = ''
                        if CNTRL_CODE in rek.login_url: rek.login_url = ''
                        if CNTRL_CODE in rek.password: rek.password = ''
                        if CNTRL_CODE in rek.notes: rek.notes = ''
                        keeper_login.update_records[vid] = rek
                # erase CNTRL_CODE
                if CNTRL_CODE in rec.title: rec.title = ''
                if CNTRL_CODE in rec.login_url: rec.login_url = ''
                if CNTRL_CODE in rec.password: rec.password = ''
                if CNTRL_CODE in rec.notes: rec.notes = ''
                keeper_login.update_records[uid] = rec
                update_count += 1
                if update_count >= UPDATE_LIMIT:
                    break

    exit(0)

if __name__ == '__main__':
    
    logger.setLevel(logging.INFO)
    api.logger.setLevel(logging.INFO)
    main(user=os.getenv('KEEPER_USER'), password=os.getenv('KEEPER_PASSWORD'), yesall=True)