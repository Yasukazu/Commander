import json
import csv
from typing import Dict, List

KEEPER_JSON = ['shared_folders', 'records']
KEEPER_RECORD = ['title', 'login', 'password', 'login_url', 'notes', 
'custom_fields', 'folders']
KEEPER_SHARED = ['uid', 'path', 'manage_users', 'manage_records', 'can_edit', 'can_share', 'permissions']
KEEPER_CUSTOM = ["TFC:Keeper"]
LOGIN_CSV = ["Title",
    "Username",
    "Email",
    "Password",
    "Website",
    "TOTP Secret Key",
    "Custom Field 1",
    "*Custom Field 2",
    "Note","Tags" ]


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

def save_csv(dics: List[Dict], fn: str):
    with open(fn, 'w') as f:
        wtr = csv.writer(f)
        wtr.writerow(*LOGIN_CSV)
        for dic in dics:
            wtr.writerow(dic['title'],


            )


