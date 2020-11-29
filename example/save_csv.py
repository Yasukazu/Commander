import json
import csv
from typing import Dict, List
from pprint import pprint
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ycommander.session import KeeperSession
from ycommander.tsrecord import TsRecord, Uid
from ycommander import params as kparams


KEEPER_JSON = ['shared_folders', 'records']
KEEPER_RECORD = ['title', 'login', 'password', 'login_url', 'notes', 
'custom_fields', 'folders']
KEEPER_SHARED = ['uid', 'path', 'manage_users', 'manage_records', 'can_edit', 'can_share', 'permissions']
KEEPER_CUSTOM = ["TFC:Keeper"]
ENPASS_CSV = ["Title", "Username", "Email", "Password", "Website", "TOTP Secret Key", "Custom Field 1", "*Custom Field 2", "Note","Tags" ]
BITWARDEN_CSV_STR = "folder,favorite,type,name,notes,fields,login_uri,login_username,login_password,login_totp"
BITWARDEN_FIELDNAMES_DICT = {n:n for n in BITWARDEN_CSV_STR.split(',')}

class ExceedError(ValueError):
    pass

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
            raise ExceedError(f"{key} exceeds {limit - len(value)}.")
        self.data[key] = but_control_char(value)

def save_bitwarden_csv(recs: List[TsRecord], fn: str, with_fields_only=False):
    # from attrdict import AttrDict
    fieldnames = BITWARDEN_CSV_STR.split(',')
    with open(fn, 'w') as f:
        wtr = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_NONNUMERIC)
        wtr.writerow(BITWARDEN_FIELDNAMES_DICT)
        fields = Fields({'notes': 5000})
        for rec in recs:
            try:
                if with_fields_only and not rec.custom_fields:
                    continue
                fields['fields'] = expand_fields(rec.custom_fields) 
                folder = ''
                try:
                   for fld in rec.folders:
                       folder = fld['folder']
                       break
                except:
                    pass
                fields['folder'] = folder
                fields['favorite'] = ''
                fields['name'] = rec.title or ''
                login_uri = rec.login_node_url if rec.login_node_url else ''
                fields['login_uri'] = login_uri
                fields['type'] = 'login' if login_uri else 'note'
                fields['login_username'] = rec.login if rec.login else ''
                fields['login_password'] = rec.password if rec.password else ''
                fields['login_totp'] = rec.totp if rec.totp else '' #  'TFC:Keeper'
                fields['notes'] = expand_s(':'.join(
                    [fields['name'], fields['login_uri'], fields['login_username']]), rec.notes) if rec.notes else ''
                wtr.writerow(fields)
            except ExceedError: # as err:
                pprint(rec.to_dictionary())
                raise

def load_keeper_records(fn: str) -> List[Dict]:
    with open(fn, 'r') as f:
        s = f.read()
        dics = json.loads(s)
    return dics['records']

import subprocess
import tempfile 
import os

NOTE_LIMIT = 4000

def expand_s(hs: str, s: str):
    es =  s.replace(r'\n', '\n')
    if len(es) > NOTE_LIMIT:
        tmpf = tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf8')
        tmpf.write(hs + '\n' + es)
        tmpf.close()
        subprocess.call(['vi', tmpf.name])
        with open(tmpf.name) as fi:
            buff = fi.read()
        os.remove(tmpf.name)
        return buff
    else:
        return es

def expand_fields(il: List) -> str:
    if not len(il):
        return []
    ol = []
    for dic in il:
        if dic['type'] != 'text':
            raise ValueError(f"{dic['type']} is not supported.")
        ol.append(f"{dic['name']}: {dic['value']}")
    return ';\n '.join(ol)

def list_all_records(sss: KeeperSession):
    return [TsRecord(sss[uid]) for uid in sss.get_every_uid()]

def main(user, password, csv_filename, with_fields_only=False):
    param = kparams.KeeperParams()
    param.user = user
    param.password = password
    sss = KeeperSession(param) 
    recs = list_all_records(sss)
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