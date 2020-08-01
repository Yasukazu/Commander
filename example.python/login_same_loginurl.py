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
        for timestamp_duplicated_uids in keeper_login.find_duplicated():
            from_old_timestamp_list = sorted(timestamp_duplicated_uids.keys())
            to_delete_tsts = from_old_timestamp_list[:-1]
            to_keep_ts = from_old_timestamp_list[-1]
            for uid in timestamp_duplicated_uids[to_keep_ts]:
                keep_rec = keeper_login.uid_to_record[uid]
                pp = pprint.pformat(keep_rec.to_dictionary())
                logger.info(f"Keep latests in duplicateds: {pp}")
            logger.info(f"{timestamp_duplicated_uids[to_keep_ts]}:original::Dupricating records of older timestamp are going to be deleted: ")
            for ts in to_delete_tsts:
                uid_set = timestamp_duplicated_uids[ts]
                for uid in uid_set:
                    rec = keeper_login.uid_to_record[uid]
                    pp = pprint.pformat(rec.to_dictionary())
                    logger.info("\t" + pp)
                logger.info(": are going to be registerd to delete_uids.")
                keeper_login.delete_uids |= uid_set
                if repeat:
                    repeat -= 1
                    if not repeat:
                        return
    exit(0)

if __name__ == '__main__':
    
    logger.setLevel(logging.INFO)
    api.logger.setLevel(logging.INFO)
    main(user=os.getenv('KEEPER_USER'), password=os.getenv('KEEPER_PASSWORD'), repeat=2)