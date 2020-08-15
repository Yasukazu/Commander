# Delete duplicating records according to same username and same login-url
# Consult other user session as the latest data
# python version >= 3.8
import sys
import os
import pprint
from keepercommander import api, params, record 
from keepercommander.record import Record
from keepercommander.session import KeeperSession
from collections import defaultdict
from typing import Dict, Set, Iterator
import logging
from fire import Fire

logger = logging.getLogger(__file__)

def user_2session_netloc(session_0: KeeperSession, session_1: KeeperSession):
    """session_0 is newer data
    """
    for timestamp_duplicated_uids in session_1.find_duplicated():
        # get login(user) and login_url(netloc)
        for uid_set in timestamp_duplicated_uids.values():
            for uid in uid_set:
                record = session_1.get_record(uid)
                login_user = record.login
                login_netloc = record.login_node_url
                break
        print(f"Combination of {login_user=} and {login_netloc} of duplicated records.")
        new_data_uid_dict = session_0.find_for_duplicated(login_user, login_netloc)
        if len(new_data_uid_dict):
            print(f"Same login-user and login-netloc is/are found in newer data.")
        from_old_timestamp_list = sorted(timestamp_duplicated_uids.keys(), reverse=True)
        to_delete_tsts = from_old_timestamp_list[1:]
        to_keep_ts = from_old_timestamp_list[0]
        print("\nLatests in duplicated: ")
        num_to_uid = [] # List[str]
        for uid in timestamp_duplicated_uids[to_keep_ts]:
            num_to_uid.append(uid)
            print(len(num_to_uid), end=': ')
            pprint.pprint(session_1.get_record(uid).to_dictionary())
        print(f"{timestamp_duplicated_uids[to_keep_ts]}:latest::Dupricating records of older timestamps: ")
        for ts in to_delete_tsts:
            uid_set = timestamp_duplicated_uids[ts]
            for uid in uid_set:
                num_to_uid.append(uid)
                print(f"\n{len(num_to_uid)}", end=': ')
                pprint.pprint(session_1.get_record(uid).to_dictionary())
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
            session_1.delete_uids |= delete_uid_set
            to_remain_uid = num_to_uid[to_remain]
            if not session_1.get_record(to_remain_uid).folder:
                fill_folder = ''
                for uid in delete_uid_set:
                    f2 = session_1.get_record(uid)
                    if f2.folder:
                        fill_folder = f2.folder
                        break
                if fill_folder:
                    session_1.get_record(to_remain_uid).folder = fill_folder
                    session_1.update_records.add(to_remain_uid)
        if repeat:
            repeat -= 1
            if not repeat:
                return

def main(user1: str, password1: str, user2: str, password2: str):
    with KeeperSession(user=user1, password=password1) as ss1:
        # duplicated_uids = ss1.find_duplicated()
        with KeeperSession(user=user2, password=password2) as ss2:
            user_2session_netloc(ss1, ss2)


if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    # api.logger.setLevel(logging.INFO)
    # record.logger.setLevel(logging.INFO)
    Fire(main)