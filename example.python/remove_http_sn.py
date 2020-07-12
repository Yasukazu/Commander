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

def main(user='', password=''):
   # from operator import attrgetter
   # inspects = [] # put UIDs to inspect as string literal like 'abc', comma separated 
    with KeeperSession(user=user, password=password) as keeper_login:
        uid_rec_dict = {u:r for (u, r) in keeper_login.get_every_record()}
        http_sn_rec_dict = {u:r for (u, r) in uid_rec_dict if r.login_url == 'http://sn'}
        for r in http_sn_rec_dict.values():
            r.login_url == '' # erase http://sn
        for u, r in uid_rec_dict.items():
           if u not in http_sn_rec_dict.keys():
               for hu, hr in http_sn_rec_dict.items():
                   if hr == r:
                       print(f"{u} and {hu} are the same Records.")
        
    exit(0)

if __name__ == '__main__':
    import logging
    
    logger = logging.getLogger(__file__)
    logger.setLevel(logging.INFO)
    main(user=os.getenv('KEEPER_USER'), password=os.getenv('KEEPER_PASSWORD'))