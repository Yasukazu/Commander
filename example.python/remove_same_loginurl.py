# Delete duplicating records according to same username and same login-url; Remain the latest record.
# set PYTHONPATH=<absolute path to 'keepercommander'>:<python lib path>
import sys
import os
import pprint
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from keepercommander import api, params, record 
from keepercommander.record import Record
from keepercommander.session import KeeperSession
from collections import defaultdict
from tabulate import tabulate
# import fire # Google python script argument library
import logging
import argparse

logger = logging.getLogger(__file__)

def remove_same_loginurl(user: str, password: str, yesall: bool=False, repeat=0):
    with KeeperSession(user=user, password=password) as keeper_login:
        for timestamp_duplicated_uids in keeper_login.find_duplicated():
            from_old_timestamp_list = sorted(timestamp_duplicated_uids.keys(), reverse=True)
            to_delete_tsts = from_old_timestamp_list[1:]
            to_keep_ts = from_old_timestamp_list[0]
            print("\nLatests in duplicated: ")
            num_to_uid = [] # List[str]
            latest_records = {}
            for uid in timestamp_duplicated_uids[to_keep_ts]:
                num_to_uid.append(uid)
                print(len(num_to_uid), end=': ')
                latest_records[uid] = keeper_login.get_record(uid)
            latests = []
            for uid, record in latest_records:
                hh, ff = zip(*record.fields())
                latests.append(ff)
            latests = tabulate(latest_records, headers=hh)
            print(latest_records)
                # pprint.pprint(keeper_login.get_record(uid).to_dictionary())
            print(f"{timestamp_duplicated_uids[to_keep_ts]}:latest::Dupricating records of older timestamps: ")
            for ts in to_delete_tsts:
                uid_set = timestamp_duplicated_uids[ts]
                for uid in uid_set:
                    num_to_uid.append(uid)
                    print(f"\n{len(num_to_uid)}", end=': ')
                    record = keeper_login.get_record(uid)
                    print(tabulate(record.fields()))
                    # pprint.pprint(keeper_login.get_record(uid).to_dictionary())
                # logger.info(": are going to be registerd to delete_uids.")
            res = input(f"Input number(1 to {len(num_to_uid)}) to remain(just return if to erase None.): ")
            try:
                to_remain = int(res)
            except:
                continue
            if to_remain <= 0 or to_remain > len(num_to_uid):
                continue
            to_remain -= 1 # adjust human number to machine number
            delete_uid_set = {v for i, v in enumerate(num_to_uid) if i != to_remain}
            assert(len(delete_uid_set) == len(num_to_uid) - 1)
            if len(delete_uid_set):
                keeper_login.delete_uids |= delete_uid_set
                to_remain_uid = num_to_uid[to_remain]
                if not keeper_login.get_record(to_remain_uid).folder:
                    fill_folder = ''
                    for uid in delete_uid_set:
                        f2 = keeper_login.get_record(uid)
                        if f2.folder:
                            fill_folder = f2.folder
                            break
                    if fill_folder:
                        keeper_login.add_move(to_remain_uid, fill_folder)
            if repeat:
                repeat -= 1
                if not repeat:
                    return

if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--user")
    parser.add_argument("--password")
    parser.add_argument("--repeat", type=int)
    args = parser.parse_args()
    # api.logger.setLevel(logging.INFO)
    # record.logger.setLevel(logging.INFO)
    remove_same_loginurl(user=args.user, password=args.password, repeat=args.repeat)
    #(user=os.getenv('KEEPER_USER'), password=os.getenv('KEEPER_PASSWORD'), repeat=2))