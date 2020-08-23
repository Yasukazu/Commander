# Delete duplicating records according to same username and same login-url; Remain the latest record.
# set PYTHONPATH=<absolute path to 'keepercommander'>:<python lib path>
import sys
import os
import pprint
from tabulate import tabulate
from typing import Dict, Tuple, Set
from numbers import Number
import logging
import argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from keepercommander.record import Record
from keepercommander.session import KeeperSession

logger = logging.getLogger(__file__)

def remove_same_loginurl(user: str, password: str, yesall: bool=False, repeat=0):
    with KeeperSession(user=user, password=password) as keeper_login:
        def field_dict(rec: Record) -> Dict[str, str]:
            ''' Customized field dict: no username, no web_address
            '''
            dt = {
                'uu..id': rec.record_uid[:2] + '..' + rec.record_uid[-2:],
                'folder': rec.folder,
                'title': rec.title[:16],
                'password': rec.password,
                'path': rec.login_url_components[2],
                'modified': keeper_login.get_modified_datetime(rec.record_uid).isoformat(timespec='minutes'),
                'notes': rec.notes.replace('\n', ';')[:16],
            }
            custom = '; '.join((f['name'] + ': ' + f['value'] for f in rec.custom_fields)) if len(
                rec.custom_fields) else ''
            dt['custom'] = custom
            return dt  # 'custom_fields': '; '.join((f"{k}: {v}" for k, v in rec.custom_fields.items()))

        all_uid_set: Set[str] = set()
        for username, login_url_node, timestamp_duplicated_uids in keeper_login.find_duplicated():
            for st in timestamp_duplicated_uids.values():
                all_uid_set |= st
            from_old_timestamp_list = sorted(timestamp_duplicated_uids.keys(), reverse=True)
            old_tsts = from_old_timestamp_list[1:]
            newest_ts = from_old_timestamp_list[0]
            newest_uids = timestamp_duplicated_uids[newest_ts]
            start_recno = recno = 1 - len(newest_uids)  # record number
            recno_str = f"-{recno}..0" if recno > 0 else f"{recno}"
            print(f"{len(newest_uids)} newest timestamp [{recno_str}] duplicated record(s): ")
            print(f"{username} {login_url_node}")
            records = []
            recno_to_record: Dict[Number, Record] = {}
            field_names: Tuple[str, ...] = ()
            for uid in newest_uids:
                record = recno_to_record[recno] = keeper_login.get_record(uid)
                record_fields_dict = field_dict(record) #[f for f in record.field_values_str()]
                if not field_names:
                    field_names = ('N', *record_fields_dict.keys())
                fields = record_fields_dict.values()  # [f for f in record.field_values_str()]
                recno += 1
                records.append([f"{recno}"] + list(fields))
            # print(tabulate(records, headers=field_names))
            # print(f"{timestamp_duplicated_uids[newest_ts]}:latest::
            # print("\nDupricating records of older
            # records2_dict = {}
            records2_num_list = []
            records2_num_to_uid = {} # record2_num : uid
            for index2, ts in enumerate(old_tsts):
                uid_set = timestamp_duplicated_uids[ts]
                for index3, uid in enumerate(uid_set):
                    record2_num = index2 + (index3 + 1) / 10
                    recno_to_record[record2_num] = keeper_login.get_record(uid)
                    # fields = [f for f in record.field_values_str()]
                    records2_num_to_uid[record2_num] = uid
                    records2_num_list.append(record2_num)
                    # records2_dict[record2_num] = ([f"{index2}.{index3 + 1}"] + fields)
            # convert each recno_to_record to list for tabulate
            table = [(f"{k}", *field_dict(v).values()) for k, v in recno_to_record.items()]
            tabulated_table = tabulate(table, headers=field_names)
            # old_records = tabulate(records2_dict.values(), headers=Record.FIELD_KEYS)
            print(tabulated_table)
            res = input(f"Input number({start_recno} to {index2}.{index3 + 1}) to remain(just return if erase none.): ")
            try:
                to_remain = float(res)
            except:
                continue
            # if to_remain <= 0 or to_remain > len(num_to_uid): continue
            to_remain_uid = recno_to_record[to_remain].record_uid  # newest_uids[-to_remain]
            delete_uid_set = all_uid_set - set((to_remain_uid,))
            """
            if to_remain <= 0:
                delete_uid_set = {u for i, u in enumerate(newest_uids) if i != -to_remain}
                old_uid_set = set(records2_num_to_uid.values())
                delete_uid_set |= old_uid_set
            else:
                newest_uid_set = set(newest_uids)
                delete_uid_set = {u for n, u in records2_num_to_uid.items() if n != to_remain}
                delete_uid_set |= newest_uid_set
                # to_remain_uid = records2_num_to_uid[to_remain]
            """
            assert(len(delete_uid_set) == len(all_uid_set) - 1)
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