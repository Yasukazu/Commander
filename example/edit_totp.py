# Show all UIDs and records in Vault
import sys
import os
import getpass
import json
import datetime
from typing import Iterator, List, Dict
import pyotp
from ycommander import params,api,record
from ycommander.record import Record

class KeeperSession(params.KeeperParams):
    ''' Login and sync_down automatically 
        user-ID is gotten from $KEEPER_USER
        user password if from $KEEPER_PASSWORD
        or parameters as with(user, password) '''
    USER = 'KEEPER_USER'
    PASSWORD = 'KEEPER_PASSWORD'
  
    
    def get_modified_timestamp(self, record_uid):
        current_rec = self.record_cache[record_uid]
        return current_rec['client_modified_time']
    
    def get_modified_time(self, record_uid):
        return datetime.datetime.fromtimestamp(self.get_modified_timestamp(record_uid) / 1000)

    
    def __init__(self, user=None, password=None, user_prompt='User:', password_prompt='Password:'):
        super().__init__()
        self.user = user or os.getenv(self.__class__.USER) or input(user_prompt)
        self.password = password or os.getenv(self.__class__.PASSWORD) or getpass.getpass(password_prompt)
        
    def __enter__(self):
        api.login(self) # user=self.user, password=self.password)
        api.sync_down(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.clear_session()  # clear internal variables
    
    def get_every_unencrypted(self):
        for uid, packet in self.record_cache.items():
            yield uid, json.loads(packet['data_unencrypted'].decode('utf-8'))

            
    def get_all_uids(self):
        return self.record_cache.keys()
        
    def get_record(self, uid):
       dt = datetime.datetime.fromtimestamp(self.record_cache[uid]['client_modified_time'] / 1000)
       rec = api.get_record(self, uid)
       rec.modified_time = dt
       return rec
       
       '''
        self.record_uid = record_uid
        self.folder = folder
        self.title = title
        self.login = login
        self.password = password
        self.login_url = login_url
        self.notes = notes
        self.custom_fields = custom_fields or []  # type: list
        self.attachments = None
        self.revision = revision
        self.unmasked_password = None
        self.totp = None
        '''

    def each_totp_record(keeper_session):# -> Iterator[str]:
        for uid in keeper_session.get_all_uids():
            record = keeper_session.get_record(uid)
            if record.totp:
                record.modified_time = record.modified_time.isoformat()
                yield json.dumps(record.__dict__, sort_keys=True, indent=4, ensure_ascii=False)


    def edit_totp(keeper_session, totp_json: str) -> List[Record]:
        aotp_dict = dict_aotp(totp_json)
        username = aotp_dict.pop('name')
        secret = aotp_dict.pop('secret')
        website = aotp_dict['issure_name']
        reclist = []
        for uid in keeper_session.get_all_uids():
            record = keeper_session.get_record(edit_uid)

            totp_uri = json_to_totp(totp_json) 
            record.totp = totp_uri
        

    def find_match_totp_record(self, otp_accounts: Dict[str, str]) -> Iterator[Record]:
        for otp_dict in otp_accounts:
            dict_aotp(otp_dict)
            username = otp_dict.pop('name')
            secret = otp_dict.pop('secret')
            issure = otp_dict['issure_name']
            for uid in keeper_session.get_all_uids():
                record = keeper_session.record_at(uid)
                if record.totp:
                    record_totp_dict = decode_totp_uri(record.totp)
                    totp_base = record.totp[len("otpauth://totp/") - 1 : record.totp.index('?')].split(':')
                    if issure == totp_base[0] and username == totp_base[1]:
                        yield record
           


def dict_aotp(aotp_dict: Dict[str, str]):
  ''' convert andOTP json format to dict for pyotp uri builder
  '''
  # aotp_dict = json.loads(json_str)
  label = aotp_dict.pop('label')
  aotp_dict['name'] = label.split(':')[1] if label.find(':') >= 0 else label
  aotp_dict['issuer_name'] = aotp_dict.pop('issuer')
  unused_keystr = "type thumbnail last_used used_frequency tags"
  for key in unused_keystr.split(' '):
      del aotp_dict[key]


def decode_totp_uri(uri: str) -> Dict[str, str]:
    content = uri[len("otpauth://totp/"):]

    dic = {k_v.split('=')[0]:k_v.split('=')[1] for k_v in content[content.index('?') + 1 :].split('&')}
    issuer_name = content[:content.index('?')]#.split(':')                    
    try:
        dic['issuer_name'], dic['name'] = issuer_name.split(':')
    except ValueError:
        dic['issuer_name'] = None
        dic['name'] = issuer_name
    return dic


def json_to_totp(json_str: str) -> str:
  aotp_dict = json.loads(json_str)
  label_split = aotp_dict.pop('label').split(':')
  name = label_split[len(label_split) - 1]
  aotp_dict['issuer_name'] = aotp_dict.pop('issuer')
  secret = aotp_dict.pop('secret')
  unused_keystr = "type thumbnail last_used used_frequency tags"
  for key in unused_keystr.split(' '):
      del aotp_dict[key]
  '''
  "type":"TOTP","algorithm":"SHA1","thumbnail":"Default","last_used":1591871947142,"used_frequency":3,"period":30,"tags":[]}
  '''
  return pyotp.utils.build_uri(secret, name, **aotp_dict)
        


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Needs arguments: user, password and totp-json-filename.")
        sys.exit(1)
    user = sys.argv[1]
    password = sys.argv[2]
    totp_json_file = sys.argv[3]
    otp_accounts = json.loads(open(totp_json_file, 'r').read())
    totp_accounts = [acc for acc in otp_accounts if acc['type'] == 'TOTP']
    for account in totp_accounts:
        dict_aotp(account)
    # otp_accounts_dict = {(iss, usr), account for account in otp_accounts}
    with KeeperSession(user=user, password=password) as session:
        for uid in session.get_all_uids():
            record = session.get_record(uid)
            if record.totp:
                record_totp_dict = decode_totp_uri(record.totp)
                for account in totp_accounts:
                    if (account['issuer_name'] == record_totp_dict['issuer_name'] and
                        account['name'] == record_totp_dict['name']):
                        print(f"totp in record: {record_totp_dict}")
                        print(f"totp in json: {account}")
    exit(0)
