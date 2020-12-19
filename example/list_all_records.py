# Show all UIDs and records in Vault
# set PYTHONPATH=<absolute path to keepercommander> AWS: /home/ec2-user/environment/Commander:/home/ec2-user/environment/.venv/lib/python3.6/dist-packages
import sys
import os
import getpass
import json
import datetime
import logging
import pylogrus
logging.setLoggerClass(pylogrus.PyLogrus)
from ycommander import params, api, record, error, session

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)


def list_all_records(user: str, password: str):
    prm = params.KeeperParams(user=user, password=password)
    ss = session.KeeperSession(prm) 
    for uid in ss.get_every_uid():
        yield ss[uid] #  func(rv)

if __name__ == '__main__':
    import getpass
    import pprint
    user = input('User:')
    password = getpass.getpass('Password:')
    for rec in list_all_records(user, password):
        pprint.pp(rec.to_dict())
        