# save Keeper vault as generic csv file for Bitwarden
import json
import csv
from typing import Dict, List
import pprint
from io import StringIO
import sys, os
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import logging
logger = logging.getLogger(__name__)
from ycommander.session import KeeperSession
from ycommander.tsrecord import TsRecord, Uid
from ycommander.params import KeeperParams


KEEPER_JSON = ['shared_folders', 'records']
KEEPER_RECORD = ['title', 'login', 'password', 'login_url', 'notes', 
'custom_fields', 'folders']
KEEPER_SHARED = ['uid', 'path', 'manage_users', 'manage_records', 'can_edit', 'can_share', 'permissions']
KEEPER_CUSTOM = ["TFC:Keeper"]
ENPASS_CSV = ["Title", "Username", "Email", "Password", "Website", "TOTP Secret Key", "Custom Field 1", "*Custom Field 2", "Note","Tags" ]
BITWARDEN_CSV_STR = "folder,favorite,type,name,notes,fields,login_uri,login_username,login_password,login_totp"
BITWARDEN_FIELDNAMES_DICT = {n:n for n in BITWARDEN_CSV_STR.split(',')}

NEWLINE_MARK = r'\n'

class ExceedError(ValueError):
    def __init__(self, key, msg):
        self.key = key
        super().__init__(msg)

from collections import UserDict
import unicodedata

def but_control_char(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")

class Fields(UserDict):
    def __init__(self, key_to_limit: Dict[str, int], default_limit=500):
        self.key_to_limit = key_to_limit
        self.default_limit = default_limit
        self.data = {}
        
    def __setitem__(self, key: str, value: str):
        limit = self.key_to_limit[key] if key in self.key_to_limit else self.default_limit
        if len(value) > limit:
            raise ExceedError(key, f"{key} exceeds {limit - len(value)}.")
        self.data[key] = but_control_char(value)

def save_bitwarden_csv(recs: List[TsRecord], fn: str, with_fields_only=False):
    # from attrdict import AttrDict
    fieldnames = BITWARDEN_CSV_STR.split(',')
    fout = StringIO()
    wtr = csv.DictWriter(fout, fieldnames=fieldnames, quoting=csv.QUOTE_NONNUMERIC)
    wtr.writerow(BITWARDEN_FIELDNAMES_DICT)
    fields = Fields({'notes': 5000})
    for rec in recs:
        additional_notes = {}
        try:
            if with_fields_only and not rec.custom_fields:
                continue
            fields['fields'] = expand_fields(rec.custom_fields) 
            fields['folder'] = rec.folder
            fields['favorite'] = ''
            fields['name'] = rec.title or ''
            # login_uri = rec.login_node_url if rec.login_node_url else ''
            fields['login_uri'] = rec.login_url
            fields['type'] = 'login' if rec.login_url else 'note'
            fields['login_username'] = rec.login if rec.login else ''
            fields['login_password'] = rec.password if rec.password else ''
            fields['login_totp'] = rec.totp if rec.totp else '' #  'TFC:Keeper'
            fields['notes'] = ';\n '.join([rec.notes] + [f"{k}: {v}" for k, v in additional_notes.items() if len(additional_notes.keys())]) #  expand_s(':'.join( [fields['name'], fields['login_uri'], fields['login_username']]), rec.notes) if rec.notes else ''
        except ExceedError as err:
            if err.key == 'login_uri':
                url, param = rec.login_url.split('?', 1)
                fields[err.key] = url
                additional_notes[err.key] = param
            else:
                rec_dic_without_err_key = {k: v for k, v in rec.items() if k != err.key}
                edited_str = edit_str(pprint.pformat(rec_dic_without_err_key) + ';' + err.key)
                try:
                    fields[err.key] = edited_str
                except ExceedError as err2:
                    logger.error(f"{err2} is still too long after edited.")
                    raise
        finally:
            wtr.writerow(fields)

            
    buff = fout.getvalue()
    fin = StringIO(initial_value=buff)
    with open(fn, 'w', encoding='utf8') as fout:
        while line := fin.readline():
            fout.write(line.replace(NEWLINE_MARK, '\n'))



def load_keeper_records(fn: str) -> List[Dict]:
    with open(fn, 'r') as f:
        s = f.read()
        dics = json.loads(s)
    return dics['records']

import subprocess
import tempfile 
import os

NOTE_LIMIT = 4000

def expand_s(hs: str, s: str) -> str:
    es =  s.replace(r'\n', '\n')
    if len(es) > NOTE_LIMIT:
        es = edit_str(hs + '\n' + es)
    es.replace('\n', NEWLINE_MARK)
    return es

def edit_str(s: str, newline_convert=True) -> str:
    try:
        editor = os.environ['EDITOR']
    except KeyError:
        editor = 'vi'
    tmpf = tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf8')
    tmpf.write(s.replace(NEWLINE_MARK, '\n')) if newline_convert else tmpf.write(s)
    tmpf.close()
    subprocess.call([editor, tmpf.name])
    with open(tmpf.name) as fi:
        buff = fi.read()
    os.remove(tmpf.name)
    return buff.replace('\n', NEWLINE_MARK) if newline_convert else buff

def expand_fields(il: List) -> str:
    if not len(il):
        return []
    ol = []
    for dic in il:
        if dic['type'] != 'text':
            raise ValueError(f"{dic['type']} is not supported.")
        ol.append(f"{dic['name']}: {dic['value']}")
    return NEWLINE_MARK.join(ol)

def list_all_records(sss: KeeperSession):
    return [TsRecord(sss[uid]) for uid in sss.get_every_uid()]

def main(user, password, csv_filename, with_fields_only=False):
    config={'user': user, 'password': password}
    param = KeeperParams(config)
    sss = KeeperSession(param) 
    recs = [TsRecord(sss[uid]) for uid in sss.get_every_uid()]
    save_bitwarden_csv(recs, csv_filename, with_fields_only=with_fields_only)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('user')
    parser.add_argument('password')
    parser.add_argument('csv_filename')
    parser.add_argument('--with-fields-only', default=False)
    args = parser.parse_args()
    main(args.user, args.password, args.csv_filename, with_fields_only=args.with_fields_only)