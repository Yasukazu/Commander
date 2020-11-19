import pprint
import logging
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ycommander import params as kparams
from ycommander import api
from ycommander import session

from pickle import dumps, loads
from Cryptodome.Cipher import AES

def encrypt(key: bytes, data: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_EAX)
    encrypted, tag = cipher.encrypt_and_digest(data)
    return dumps((tag, encrypted, cipher.nonce))

def decrypt(key: bytes, data: bytes) -> bytes:
    tag, encrypted, nonce = loads(data)
    decipher = AES.new(key, AES.MODE_EAX, nonce)
    return decipher.decrypt_and_verify(encrypted, tag)

YKEEPER_CONFIG = 'ykeeper.cnf'

def login_test(user='', password='', totp_secret=''): #, device='', token='') : #user, password, device='', token=''):
    breakpoint()
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


from ycommander.api import OtpInput

import redis

class ROtpInput(OtpInput):
    KEEPER_PREFIX = 'Keeper:'
    def __init__(self, name: str):
        breakpoint()
        rds = redis.Redis(host='localhost', port=6379, db=0)
        key = ROtpInput.KEEPER_PREFIX + name
        self.secret = rds.get(key).decode('ascii')
        self.name = name


def main(user, password='', totp_secret=''):
    breakpoint()
    if totp_secret:
        otp_input = OtpInput(name=user, secret=totp_secret)
    else:
        otp_input = ROtpInput(user)
    prms = kparams.KeeperParams()
    cfg = api.login(prms, user=user, password=password, otp_input=otp_input)
    print("login success")
    pprint.pprint(cfg)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', help='user name as user@example.com')
    parser.add_argument('--password', help='password for the user')
    parser.add_argument('--secret', help='one time password secret code')
    args = parser.parse_args()
    user = args.user or input("user:")
    password = args.password or input("password:")
    totp_secret = args.secret
    breakpoint()
    main(user, password=password, totp_secret=totp_secret)
