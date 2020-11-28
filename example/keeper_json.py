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

class KeeperRecord:
    def __init__(self, dic: Dict):
        self._dic = dic
    
    @property
    def title(self):
        return self._dic['title']



    

def load_keeper_records(fn: str) -> List[Dict]:
    with open(fn, 'r') as f:
        dics = json.load(f)
    return dics['records']

def expand_s(s: str):
    return s.replace(r'\n', '\n')

def expand_fields(d: Dict) -> List[str]:
    lst = [k + ': ' + v for k, v in d.items()]
    return '\n'.join(lst)


def save_bitwarden_csv(dics: List[Dict], fn: str):
    from attrdict import AttrDict
    with open(fn, 'w') as f:
        wtr = csv.writer(f)
        headers = BITWARDEN_CSV_STR.split(',')
        wtr.writerow(*headers)
        fields = []
        for dic in dics:
            adic = AttrDict(dic)
            folder = ''
            try:
               for fld in adic.folders:
                   folder = fld
                   break
            except:
                pass
            fields.append(folder)
            fields.append('') # favorite = ''
            fields.append('login') # type = 'login'
            fields.append(dic.get('title', ''))
            fields.append(expand_s(adic.notes))
            fields.append(expand_fields(adic.fields))
            fields.append(adic.login_url)
            fields.append(adic.login)
            fields.append(adic.password)

            wtr.writerow(


            )


