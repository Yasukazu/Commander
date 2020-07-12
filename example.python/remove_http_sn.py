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
from pprint import pprint

def main(user: str, password: str, yesall: bool=False):
   # from operator import attrgetter
   # inspects = [] # put UIDs to inspect as string literal like 'abc', comma separated 
    with KeeperSession(user=user, password=password) as keeper_login:
        uid_rec_dict = {u:r for (u, r) in keeper_login.get_every_record()}
        http_sn_rec_dict = {u:r for (u, r) in uid_rec_dict.items() if r.login_url == 'http://sn'}
        if len(http_sn_rec_dict) > 0:
            print("Invalid login url('http://sn') records found")
            for hu, hr in http_sn_rec_dict.items():
                hr.login_url = '' # reset login url
                for u, r in uid_rec_dict.items():
                    if u != hu:
                        if hr == r:
                            print("Duplicating records are found:")
                            pprint(r)
                            api.delete_record(keeper_login, hu)
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
    import logging
    
    logger = logging.getLogger(__file__)
    logger.setLevel(logging.INFO)
    main(user=os.getenv('KEEPER_USER'), password=os.getenv('KEEPER_PASSWORD'), yesall=True)