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

def login_test(user='', password=''): #, device='', token='') : #user, password, device='', token=''):
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
    
    
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('user', help='user name as user@example.com', default=os.getenv('KEEPER_USER')) 
    parser.add_argument('password', help='password for the user', default=os.getenv('KEEPER_PASSWORD'))
    args = parser.parse_args()
    user = args.user
    password = args.password
    login_test(user, password)
    # import fire
    # breakpoint()
    # fire.Fire(login_test)
    # login_test(args.user, args.password)
    exit(0)
    # plac.call(login_test)
    # parser.add_argument('--device', dest='device', help='device of last login')
    # parser.add_argument('--token', dest='token', help='token of last login')
    # args = parser.parse_args() 
    # login_test(args.user, args.password)

    # capr = configargparse.get_argument_parser()
    # capr.add_argument()
    # args, opts = capr.parse_known_args()
    # from ycommander import PARSER as main_parser
    # breakpoint()
    # args, opts = main_parser.parse_known_args()