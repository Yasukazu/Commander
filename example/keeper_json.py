import json
import csv
from typing import Dict, List

KEEPER_JSON = ['shared_folders', 'records']
KEEPER_RECORD = ['title', 'login', 'password', 'login_url', 'notes', 
'custom_fields', 'folders']
KEEPER_SHARED = ['uid', 'path', 'manage_users', 'manage_records', 'can_edit', 'can_share', 'permissions']
KEEPER_CUSTOM = ["TFC:Keeper"]
ENPASS_CSV = ["Title", "Username", "Email", "Password", "Website", "TOTP Secret Key", "Custom Field 1", "*Custom Field 2", "Note","Tags" ]
BITWARDEN_CSV_STR = "folder,favorite,type,name,notes,fields,login_uri,login_username,login_password,login_totp"

class ExceedError(ValueError):
    pass

class Fields(list):
    def append(self, s: str, maxlen=500):
        if len(s) > maxlen:
            raise ExceedError(f"{s} exceeds {len(s) - maxlen} chars.")
        super().append(s)

from pprint import pprint

def save_bitwarden_csv(dics: List[Dict], fn: str):
    from attrdict import AttrDict
    with open(fn, 'w') as f:
        wtr = csv.writer(f)
        headers = BITWARDEN_CSV_STR.split(',')
        wtr.writerow(headers)
        fields = Fields()
        for dic in dics:
            adic = AttrDict(dic)
            try:
                folder = ''
                try:
                   for fld in adic.folders:
                       folder = fld['folder']
                       break
                except:
                    pass
                fields.append(folder)
                fields.append('') # favorite
                fields.append('login') # type 
                fields.append(dic.get('title', ''))
                fields.append(expand_s(dic.get('notes', '')), maxlen=5000)
                fields.append(expand_fields(dic.get('custom_fields', [])))
                fields.append(dic.get('login_url', ''))
                fields.append(dic.get('login', ''))
                fields.append(dic.get('password', ''))
                totp = ''
                try:
                    totp = adic.custom_fields['TFC:Keeper']
                except:
                    pass
                fields.append(totp)
                wtr.writerow(fields)
            except ExceedError: # as err:
                pprint(adic)
                raise





def load_keeper_records(fn: str) -> List[Dict]:
    with open(fn, 'r') as f:
        s = f.read()
        dics = json.loads(s)
    return dics['records']

def expand_s(s: str):
    return s.replace(r'\n', '\n')

def expand_fields(d: Dict) -> List[str]:
    if not len(d):
        return []
    lst = [k + ': ' + v for k, v in d.items()]
    return '\n'.join(lst)

if __name__ == '__main__':
    import sys
    rr = load_keeper_records(sys.argv[1])
    save_bitwarden_csv(rr, sys.argv[2])