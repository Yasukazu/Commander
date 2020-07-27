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

INVALID_URL = 'http://sn'
CNTRL_CODE = '\x10' # data link escape (+)

def main(user: str, password: str, yesall: bool=False):
   # from operator import attrgetter
   # inspects = [] # put UIDs to inspect as string literal like 'abc', comma separated 
    with KeeperSession(user=user, password=password) as keeper_login:
        uid_rec_dict = {u:r for (u, r) in keeper_login.get_every_record()}
        update_count = 0
        UPDATE_LIMIT = 2
        for rec in uid_rec_dict.values():
            if CNTRL_CODE in (rec.title, rec.login_url, rec.password, rec.notes):
                print(f"Record {rec.record_uid}(Title: {rec.title}) has a Control-code name (Title, Login_url, password, notes): {rec}")
            folders = keeper_login.get_folders(rec.record_uid)
            if CNTRL_CODE in folders:
                print(f"Record {rec.record_uid}(Title: {rec.title}) has a Control-code name folder: {folders}")
        
        http_sn_rec_dict = {u:r for (u, r) in uid_rec_dict.items() if r.login_url == INVALID_URL}
        if len(http_sn_rec_dict) > 0:
            for hu, hr in http_sn_rec_dict.items():
                logger.info(f"Invalid login url('{INVALID_URL}') in a record('{hu}') is going to be erased.")
                hr.login_url = '' # reset login url
                keeper_login.add_update(hr)
                for u, r in uid_rec_dict.items():
                    if u == hu:
                        continue
                    if (hr.title == r.title and
                        hr.login == r.login and
                        hr.notes == r.notes and
                        hr.password == r.password and
                        hr.custom_fields == r.custom_fields and
                        hr.attachments == r.attachments):
                            hu_str = pprint.pformat(hu)
                            logger.info(f"Duplicating record is found:{hu_str}")
                            if not r.folder or r.folder == hr.folder:
                                keeper_login.add_delete(u)
                            # api.delete_record(keeper_login, hu)
            ''' list is not hash-able: create tuple key dict.
            http_sn_uid_set_dict = {(
                    r.folder,
                    r.title,
                    r.login,
                    r.password,
                    r.login_url,
                    r.notes,
                    r.custom_fields,
                    r.attachments
                ):{r.record_uid} for r in http_sn_rec_dict.values()}
            dupsetdict = defaultdict(set)
            for uid, r in uid_rec_dict.items():
                kt = (
                    r.folder,
                    r.title,
                    r.login,
                    r.password,
                    r.login_url,
                    r.notes,
                    r.custom_fields,
                    r.attachments
                )
                if kt in http_sn_uid_set_dict and http_sn_uid_set_dict[kt] != uid:
                    dupsetdict[kt].add(r.record_uid)
            if len(dupsetdict) > 0:
                for kk, uid in dupsetdict.items():
                    print("Duplicating")
                    pprint(kk)

            # Reset login_url version:
            for hsk, hsr in http_sn_rec_dict.items():
                print(f"'http://sn' login_url: Title: '{hsr.title}'; uid:'{hsk}'")
                unset_yn = 'y' if yesall else input('UnSet http://sn?(y/n):')
                if unset_yn == 'y':
                    hsr.login_url = ''
                    api.update_record(keeper_login, hsr)
                    print(f"{hsk} record is updated.") 
                # Delete API version:
                for hk, hr in http_sn_rec_dict.items():
                    # search same item except login_url
                    def unmatch(k, r):
                        for _at in "folder login notes password title custom_fields attachments".split():
                            if getattr(r, _at) != getattr(hr, _at):
                                return True
                    for u, o_r in uid_rec_dict.items():
                        if u != hk and not unmatch(u, o_r):
                        print(f"'{hr.title}': {u} and {hk}(with 'http://sn' login_url) are the same Records.") '''
        
    exit(0)

if __name__ == '__main__':
    
    logger.setLevel(logging.INFO)
    api.logger.setLevel(logging.INFO)
    main(user=os.getenv('KEEPER_USER'), password=os.getenv('KEEPER_PASSWORD'), yesall=True)