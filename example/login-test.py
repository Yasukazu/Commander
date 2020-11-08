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
    
    

from ycommander.record import get_totp_code
from ycommander.api import OtpInput
class TotpInput(OtpInput):
    def __init__(self):
        pass
    def input(self):
        pass

def main(user, password='', totp_secret=''):
    otp_input = OtpInput(name=user, secret=totp_secret)
    prms = kparams.KeeperParams()
    cfg = api.login(prms, user=user, password=password, otp_input=otp_input)
    print("login success")
    pprint.pprint(cfg)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('user', help='user name as user@example.com')
    parser.add_argument('password', help='password for the user')
    parser.add_argument('secret', help='one time password secret code')
    args = parser.parse_args()
    user = args.user
    password = args.password
    totp_secret = args.secret
    otp_input = OtpInput(name=user, secret=totp_secret)
    prms = kparams.KeeperParams()
    cfg = api.login(prms, user=user, password=password, otp_input=otp_input)
