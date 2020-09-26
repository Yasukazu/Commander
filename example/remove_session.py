# Delete duplicating records according to same username and same login-url; Remain the latest record.
# set PYTHONPATH=<absolute path to 'keepercommander'>:<python lib path>
import sys
import os
from tabulate import tabulate
from typing import Dict, Tuple, Set, List, Optional
import logging
import argparse
import re
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from keepercommander.session import KeeperSession
from keepercommander.tsrecord import TsRecord, Uid

logger = logging.getLogger(__file__)


class RemoveSession(KeeperSession):
    def remove_same_loginurl(self: KeeperSession, immediate_remove: bool = False, repeat: int = 0, move: bool = False):
        # with KeeperSession(user=user, password=password) as self.:
        def field_dict(rec: TsRecord) -> Dict[str, str]:
            # Customized field dict: no username, no web_address
            dt = {
                'uu..id': rec.record_uid[:2] + '..' + rec.record_uid[-2:],
                'folder': rec.folder,
                'title': rec.title[:16],
                'password': rec.password,
                'path': rec.login_url_components[2],
                'modified': rec.timestamp.date.isoformat(timespec='minutes'),
                'notes': rec.notes.replace('\n', ';')[:16],
            }
            custom = '; '.join((f['name'] + ': ' + f['value'] for f in rec.custom_fields)) if len(
                rec.custom_fields) else ''
            dt['custom'] = custom
            # ToDo: appended files (attachments)
            return dt

        all_uid_set: Set[Uid] = set()
        for username, login_url_node, timestamp_duplicated_uids in self.find_duplicated():
            index = 1
            for st in timestamp_duplicated_uids.values():
                all_uid_set |= st
            from_old_timestamp_list = sorted(timestamp_duplicated_uids.keys(), reverse=True)
            old_tsts = from_old_timestamp_list[1:]
            newest_ts = from_old_timestamp_list[0]
            newest_uids = timestamp_duplicated_uids[newest_ts]
            username_url = f"{username} {login_url_node}"
            print(username_url)
            recno_to_record: Dict[Tuple[int, int], TsRecord] = {}  # (timestamp_group, item_number)
            field_names: Tuple[str, ...] = ()
            for i, uid in enumerate(newest_uids):
                rec = recno_to_record[(index, i + 1)] = self.record_at(uid)
                if i == 0:
                    record_fields_dict = field_dict(rec)  # [f for f in record.field_values_str()]
                    field_names = ('T.N', *record_fields_dict.keys())
            for ts in old_tsts:
                uid_set: Set[Uid] = timestamp_duplicated_uids[ts]
                index += 1
                for i, uid in enumerate(uid_set):
                    recno_to_record[(index, i + 1)] = self.record_at(uid)
            # convert each recno_to_record to list for tabulate
            table = [(f"{k[0]}.{k[1]}", *field_dict(v).values()) for k, v in recno_to_record.items()]
            tabulated_table = tabulate(table, headers=field_names)
            print(tabulated_table)
            recno_list = [f"{k[0]}.{k[1]} " for k in recno_to_record.keys()]
            recno_completer = WordCompleter(recno_list)
            res = prompt(f"Input number(T.N format) to remove(Tab to show candidates): ", completer=recno_completer,
                         bottom_toolbar="Enter without candidate to skip.")
            if not res:
                print(f"Doing nothing because nothing is chosen.")
                continue
            matcher = re.compile(r"(\d+)\.(\d+)")
            mm = matcher.findall(res)
            if not len(mm):
                print(f"Doing nothing because nothing got matching from shown choices.")
                continue
            res_recno = [(int(m[0]), int(m[1])) for m in mm]
            res_recs = [recno_to_record[r] for r in res_recno]
            to_delete_uid_set = set([r.uid for r in res_recs])
            if move:
                to_remain_uid_set: Set[Uid] = all_uid_set - to_delete_uid_set  # recno_to_record[tpl].uid
                # to_delete_uid_set: Set[Uid] = set([r.uid for r in recno_to_record.values()]) - set((to_remain_uid,))
                if len(to_delete_uid_set) and len(to_remain_uid_set) == 1:
                    to_remain_uid = list(to_remain_uid_set)[0]
                    if not self.record_at(to_remain_uid).folder:  # ToDo: folder becomes empty str
                        fill_folder = ''
                        for uid in to_delete_uid_set:
                            f2 = self.record_at(uid)
                            if f2.folder:
                                fill_folder = f2.folder
                                break
                        if fill_folder:
                            if move:
                                self.move_immediately(to_remain_uid, fill_folder)
                            else:
                                self.add_move(to_remain_uid, fill_folder)
            if immediate_remove:
                self.delete_immediately(to_delete_uid_set)
            else:
                self.add_delete_set(to_delete_uid_set)
            if repeat:
                repeat -= 1
                if not repeat:
                    return


if __name__ == '__main__':
    import fire

    fire.Fire(RemoveSession)
    exit(0)

    def remove_same_loginurl_main(every=False, repeat=0, move=False):  # argv: List[str] = sys.argv,
        """
        Remove records with same user and same password
        :param argv: startup parameter
        :param remove_immediatley: immediately remove records after every prompt
        :param repeat: repeats limited times to look for user and password
        :param move: move remaining record to folder of other record(s)
        """
        with KeeperSession() as sesyon:
            remove_same_loginurl(sesyon, immediate_remove=every, repeat=repeat, move=move)

