# Delete duplicating records according to same username and same login-url; Remain the latest record.
# set PYTHONPATH=<absolute path to 'keepercommander'>:<python lib path>
import sys
import os
import pprint
from keepercommander import api, params 
from keepercommander.record import Record
from keepercommander.session import KeeperSession
from collections import defaultdict
import logging

logger = logging.getLogger(__file__)

def main(user: str, password: str, yesall: bool=False, repeat=0):
    with KeeperSession(user=user, password=password) as keeper_login:
        for timestamp_duplicated_uids in keeper_login.find_duplicated():
            from_old_timestamp_list = sorted(timestamp_duplicated_uids.keys(), reverse=True)
            to_delete_tsts = from_old_timestamp_list[1:]
            to_keep_ts = from_old_timestamp_list[0]
            print("Latests in duplicated: ")
            num_to_uid = [] # List[str]
            for uid in timestamp_duplicated_uids[to_keep_ts]:
                num_to_uid.append(uid)
                print(len(num_to_uid), end=': ')
                pprint.pprint(keeper_login.get_record(uid).to_dictionary())
            print(f"{timestamp_duplicated_uids[to_keep_ts]}:original::Dupricating records of older timestamp are going to be deleted: ")
            for ts in to_delete_tsts:
                uid_set = timestamp_duplicated_uids[ts]
                for uid in uid_set:
                    num_to_uid.append(uid)
                    print(len(num_to_uid), end=': ')
                    pprint.pprint(keeper_login.get_record(uid).to_dictionary())
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
                        keeper_login.get_record(to_remain_uid).folder = fill_folder
                        keeper_login.update_records.add(to_remain_uid)
            if repeat:
                repeat -= 1
                if not repeat:
                    return
    exit(0)

if __name__ == '__main__':
    
    logger.setLevel(logging.INFO)
    api.logger.setLevel(logging.INFO)
    main(user=os.getenv('KEEPER_USER'), password=os.getenv('KEEPER_PASSWORD'), repeat=2)