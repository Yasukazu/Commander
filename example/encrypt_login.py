import pprint
import logging
import getpass
from dataclasses import dataclass
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ycommander import params as kparams
from ycommander import api
from ycommander import session

from pickle import dumps, loads
from Cryptodome.Cipher import AES

def encrypt(key: bytes, data: bytes) -> bytes:
    if len(key) < 32:
        raise ValueError('key length must be 32 or more.')
    cipher = AES.new(key[:32], AES.MODE_EAX)
    encrypted, tag = cipher.encrypt_and_digest(data)
    return dumps((tag, encrypted, cipher.nonce))

def decrypt(key: bytes, data: bytes) -> bytes:
    if len(key) < 32:
        raise ValueError('key length must be 32 or more.')
    tag, encrypted, nonce = loads(data)
    decipher = AES.new(key[:32], AES.MODE_EAX, nonce)
    return decipher.decrypt_and_verify(encrypted, tag)

YKEEPER_CONFIG = 'ykeeper.cnf'

@dataclass
class PasswordOtp:
    password: str
    otp: str

from diceware import get_passphrase
from collections import UserDict
from typing import Dict, Optional
class EncryptedDict(UserDict):
    ENCODING = 'ascii'
    def __init__(self, passphrase: str='', db: Optional[bytes]=None, dct: Optional[Dict]=None):
        if not passphrase and db:
            raise ValueError('Db needs passphrase!')
        if not passphrase:
            print('Getting passphrase from diceware..')
            passphrase = get_passphrase()
            print(passphrase)
        self.passphrase = passphrase
        super().__init__()
        self.data = {}
        if db:
            self.load(db)
        if dct:
            self.data.update(dct)
    
    def dump(self) -> bytearray:
        main_data = dumps(self.data)
        main_key = self.passphrase.encode(EncryptedDict.ENCODING)
        return encrypt(main_key, main_data)

    def load(self, db: bytes):
        data = decrypt(self.passphrase.encode(EncryptedDict.ENCODING), db)
        self.data.update(loads(data))
            

def create_encrypted_file(bin: bytes, filename: str, passphrase: str = '') -> bytes: #  user: str = '', password: str = '', otp: str = ''
    passphrase = passphrase or getpass.getpass('Input passphrase:')
    '''
    user = user or input('Input user:')
    password = password or getpass.getpass('Input password:')
    otp = otp or input('Input otp(one time password):')
    '''
    # main_dict = {}
    # main_dict[user] = PasswordOtp(password, otp)
    main_data = dumps(bin)
    main_key = passphrase.encode('ascii')
    return encrypt(main_key, main_data)

def get_from_main_db(main_db: bytes, passphrase: str, key: str):
    main_data = decrypt(passphrase.encode('utf8'), main_db)
    main_dict = loads(main_data)
    return main_dict[key]



def login_test(db_name: str='', passphrase='') : #  user='', if not user: user = input('Input user:')
    if db_name:
        if not passphrase:
            raise ValueError('Needs Passphrase to use db:' + db_name)
        with open(db_name, 'rb') as db_file:
            db = db_file.read()
            edict = EncryptedDict(passphrase=passphrase, db=db)
    else:
        edict = EncryptedDict(passphrase)
    if not passphrase:
        passphrase = input('Input passphrase')
    config_data = None
    if os.path.exists(YKEEPER_CONFIG): 
        with open(YKEEPER_CONFIG, 'rb') as fi:
            config_data = fi.read()
    param = kparams.KeeperParams()
    config = api.login(param, user=user, password=password) # , device=device, token=token)
    session.logger.setLevel(logging.INFO)
    breakpoint() # print(f"--device={config.device}  --token={config.token}")
    ssn = session.KeeperSession(param)
    pprint.pprint(ssn)
    
    # baram = pickle.dumps(param)
    # caram = base64.b64encode(baram)


if __name__ == '__main__':
    from fire import Fire
    Fire()