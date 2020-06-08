# Show all UIDs in Vault
import sys
import os
import getpass
import json
sys.path.append("..")  # pwd includes keepercommander"
#sys.path.append("../.venv/lib/python3.6/dist-packages")
from keepercommander import api, params # set PYTHONPATH=<absolute path to keepercommander>
from pprint import pprint


class KeeperLogin(object):
    ''' Login and sync_down automatically 
        user-ID is gotten from $KEEPER_USER
        user password if from $KEEPER_PASSWORD
        or parameters as with(user, password) '''

    USER = 'KEEPER_USER'
    PASSWORD = 'KEEPER_PASSWORD'

    def __enter__(self, user=None, password=None, user_prompt='User:', password_prompt='Password:'):
        self.params = params.KeeperParams()
        self.params.user = user or os.getenv(KeeperLogin.USER) or input(user_prompt)
        self.params.password = password or os.getenv(KeeperLogin.PASSWORD) or getpass.getpass(password_prompt)
        api.login(self.params)
        api.sync_down(self.params)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.params.clear_session()  # clear internal variables
    
    def get_every_unencrypted(self):
        for uid, packet in self.params.record_cache.items():
            yield uid, json.loads(packet['data_unencrypted'].decode('utf-8'))
 
    def get_every_record(self):
        for uid in self.params.record_cache:
            yield uid, api.get_record(keeper_login.params, uid) 
            

if __name__ == '__main__':
    import logging
    from operator import attrgetter
    logger = logging.getLogger(__file__)
    logger.setLevel(logging.INFO)
    inspects = [] # put UIDs to inspect as string literal like 'abc', comma separated 
    with KeeperLogin() as keeper_login:
        for uid, unencrypted in keeper_login.get_every_unencrypted():
            print(f"{uid}:{unencrypted}")
            break
            
        rec_rec = {}
        uid_date = {}
        for uid, record in keeper_login.get_every_record():
            # print(f"\n{uid}:") 
            rec_rec[uid] = record.to_dictionary()
            uid_date[uid] = keeper_login.params.get_modified_time(uid)
            
        sorted_uid_date = sorted(uid_date.items(), key=lambda kv: kv[1], reverse=True)
        for k, d in sorted_uid_date:
            rr = rec_rec[k]
            rr['modified_time'] = d.isoformat()
            print(json.dumps(rr, sort_keys=True, indent=4, ensure_ascii=False))
            # pprint(rr)
            # print(json.dumps(record.to_dictionary(), sort_keys=True, indent=4))
        
    exit(0)
