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

def main(user, password):
   # from operator import attrgetter
   # inspects = [] # put UIDs to inspect as string literal like 'abc', comma separated 
    with KeeperSession(user=user, password=password) as keeper_login:
        uid_rec_dict = {u:r for (u, r) in keeper_login.get_every_record()}
        http_sn_rec_dict = {u:r for (u, r) in uid_rec_dict.items() if r.login_url == 'http://sn'}
        if len(http_sn_rec_dict) > 0:

            for r in http_sn_rec_dict.values():
                print(f"'http://sn' login_url: Title: '{r.title}'")
        #    r.login_url == '' # erase http://sn
        # for u, r in uid_rec_dict.items():
            for hk, hr in http_sn_rec_dict.items():
                # search same item except login_url
                def unmatch(k, r):
                    if k == hk:
                        return True
                    for _at in "folder login notes password title custom_fields attachments".split():
                        if getattr(r, _at) != getattr(hr, _at):
                            return True
                for u, o_r in uid_rec_dict.items():
                    if not unmatch(u, o_r):
                       print(f"'{hr.title}': {u} and {hk}(with 'http://sn' login_url) are the same Records.")
        
    exit(0)

if __name__ == '__main__':
    import logging
    
    logger = logging.getLogger(__file__)
    logger.setLevel(logging.INFO)
    main(user=os.getenv('KEEPER_USER'), password=os.getenv('KEEPER_PASSWORD'))