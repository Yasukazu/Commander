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
from typing import Iterator, List, Dict
# import fire # Google python script argument library
import logging
import argparse

logger = logging.getLogger(__file__)

def remove_same_loginurl(user: str, password: str, yesall: bool=False, repeat=0):
    with KeeperSession(user=user, password=password) as keeper_login:
        def field_dict(self: Record) -> Dict[str, str]:
            ''' Customized field dict: no username, no web_address
            '''
            dt = {
                'uu..id': self.record_uid[:2] + '..' + self.record_uid[-2:],
                'folder': self.folder,
                'title': self.title[:16],
                'password': self.password,
                'path': self.login_url_components[2],
                'modified': keeper_login.get_modified_datetime(self.record_uid).isoformat(timespec='minutes'),
                'notes': self.notes.replace('\n', ';')[:16],
            }
            custom = '; '.join((f['name'] + ': ' + f['value'] for f in self.custom_fields)) if len(
                self.custom_fields) else ''
            dt['custom'] = custom
            return dt  # 'custom_fields': '; '.join((f"{k}: {v}" for k, v in self.custom_fields.items()))

        for timestamp_duplicated_uids in keeper_login.find_duplicated():
            from_old_timestamp_list = sorted(timestamp_duplicated_uids.keys(), reverse=True)
            old_tsts = from_old_timestamp_list[1:]
            newest_ts = from_old_timestamp_list[0]
            newest_uids = timestamp_duplicated_uids[newest_ts]
            print(f"{len(newest_uids)} newest timestamp [0 .. -{len(newest_uids) - 1}] duplicated records: ")
            records = []
            field_names = None
            for index, uid in enumerate(newest_uids):
                record = keeper_login.get_record(uid)
                if index == 0:
                    username = record.login
                    login_url = record.login_node_url
                    print(f"{username=}, {login_url=}")
                record_fields_dict = field_dict(record) #[f for f in record.field_values_str()]
                if not field_names:
                    field_names = ('No.', *record_fields_dict.keys())
                fields = record_fields_dict.values()
                # fields = [f for f in record.field_values_str()]
                records.append([f"{-index}"] + list(fields))
            last_index = index
            newest_records = tabulate(records, headers=field_names)
            print(newest_records)
                # pprint.pprint(keeper_login.get_record(uid).to_dictionary())
            # print(f"{timestamp_duplicated_uids[newest_ts]}:latest::
            print("\nDupricating records of older timestamps: ") ## ToDo: same output for index2 also
            records2_dict = {}
            records2_num_list = []
            records2_num_to_uid = {} # record2_num : uid
            for index2, ts in enumerate(old_tsts):
                uid_set = timestamp_duplicated_uids[ts]
                for index3, uid in enumerate(uid_set):
                    record = keeper_login.get_record(uid)
                    fields = [f for f in record.field_values_str()]
                    record2_num = index2 + (index3 + 1) / 10
                    records2_num_to_uid[record2_num] = uid
                    records2_num_list.append(record2_num)
                    records2_dict[record2_num] = ([f"{index2}.{index3 + 1}"] + fields)
            old_records = tabulate(records2_dict.values(), headers=Record.FIELD_KEYS)
            print(old_records)
            res = input(f"Input number({last_index} to {index2}.{index3 + 1}) to remain(just return if to erase None.): ")
            try:
                to_remain = float(res)
            except:
                continue
            # if to_remain <= 0 or to_remain > len(num_to_uid): continue
            if to_remain <= 0:
                delete_uid_set = {u for i, u in enumerate(newest_uids) if i != -to_remain}
                old_uid_set = set(records2_num_to_uid.values())
                delete_uid_set |= old_uid_set
                to_remain_uid = newest_uids[-to_remain]
            else:
                newest_uid_set = set(newest_uids)
                delete_uid_set = {u for n, u in records2_num_to_uid.items() if n != to_remain}
                delete_uid_set |= newest_uid_set
                to_remain_uid = records2_num_to_uid[to_remain]
            # assert(len(delete_uid_set) == len(num_to_uid) - 1)
            if len(delete_uid_set):
                keeper_login.delete_uids |= delete_uid_set
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