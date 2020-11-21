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
class EncryptedDict:
    ENCODING = 'utf8'
    def __init__(self, passphrase: str = '', db: bytes=None):
        if not passphrase and db:
            raise ValueError('Db needs passphrase!')
        if not passphrase:
            print('Getting passphrase from diceware..')
            passphrase = get_passphrase()
            print(passphrase)
        self.passphrase = passphrase
        if db:
            self.load(db)
        else:
            self.main_dict = {}
    
    def dump(self) -> bytearray:
        main_data = dumps(self.main_dict)
        main_key = self.passphrase.encode(EncryptedDict.ENCODING)
        return encrypt(main_key, main_data)

    def load(self, db: bytes):
        data = decrypt(self.passphrase.encode(EncryptedDict.ENCODING), db)
        self.main_dict = loads(data)
            

def create_main_db(passphrase: str = '', user: str = '', password: str = '', otp: str = '') -> bytes:
    passphrase = passphrase or getpass.getpass('Input main password:')
    user = user or input('Input user:')
    password = password or getpass.getpass('Input password:')
    otp = otp or input('Input otp(one time password):')
    main_dict = {}
    main_dict[user] = PasswordOtp(password, otp)
    main_data = dumps(main_dict)
    main_key = passphrase.encode('utf8')
    return encrypt(main_key, main_data)

def get_from_main_db(main_db: bytes, passphrase: str, key: str):
    main_data = decrypt(passphrase.encode('utf8'), main_db)
    main_dict = loads(main_data)
    return main_dict[key]



def login_test(user='', passphrase=''):
    if not user:
        user = input('Input user:')
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
