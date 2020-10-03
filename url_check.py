import logging
# logger.basicConfig(filename=f"{__name__}.log")
logger = logging.getLogger(__name__)
sHandler = logging.StreamHandler()
sHandler.setLevel(logging.INFO)
logger.addHandler(sHandler)
logfilenode = __file__.rsplit('.')[0]
handler = logging.FileHandler(f"{logfilenode}.log")
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
import sys
import os

import ycommander as kc
from ycommander import api, params
import chardet
from bs4 import BeautifulSoup  # python -m pip install bs4
import requests # request alternative
import urllib
from urllib.parse import urlparse
from urllib import request, error
import re
import os
from urlextract import URLExtract
import sqlite3
from datetime import datetime, timedelta, timezone
import validators
from  validators import url as url_validator
import tldextract

class MatchError(Exception):
    pass

class BaseExtractor:
    http_re = r"(http|https):\/\/([^\/]+)"
    pg = re.compile(http_re)
    extractor = URLExtract()
    
    @classmethod
    def extract(cls, url):
        '''Raises validators.util.ValidationFailure
        '''
        rt = cls.pg.match(url)
        if not rt:
            raise MatchError
        url = cls.extractor.find_urls(rt)
        return rt.group(1, 2)
  
def extract_base(url):
    url_validator.url(url)
    http_re = r"(http|https):\/\/([^\/]+)"
    pg = re.compile(http_re)
    rt = pg.match(url)
    if not rt:
        raise MatchError
    return rt.group(1, 2)


if __name__ == '__main__':
    try:
        user = sys.argv[1]
    except IndexError:
        try:
            user = os.environ['user']
        except KeyError:
            user = input("User:")
    try:
        password = sys.argv[2]
    except IndexError:
        try:
            password = os.environ['password']
        except KeyError:
            from getpass import getpass
            password = getpass('Password:')
    # config = {'user': user, 'password': password}
    params = params.KeeperParams()  # config=config)
    params.user = user
    params.password = password
    session_token = api.login(params)
    extractor = URLExtract()
    __SQLFILE__ = "check-keeper"
    __SQLEXT__ = '.sqlite'
    TABLE_NAME = 'invalid_url'
    conn = sqlite3.connect(f"{__SQLFILE__}{__SQLEXT__}",
        detect_types = sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    sqlite3.dbapi2.converters['DATETIME'] = sqlite3.dbapi2.converters['TIMESTAMP']
    cur = conn.cursor()
    cur.execute(f"CREATE TABLE if not exists {TABLE_NAME} (uid text unique, title text, url text, report text, error integer, updated datetime)")
    jp_tz = timezone(timedelta(hours=+9), 'JST')
    # with open(f"{__file__}.output", mode='a') as o_f:
    def put_db(uid, title, url, report, error):
        print(report)
        cur.execute(f"insert into {TABLE_NAME} VALUES (:uid, :title, :url, :report, :error, :updated)", (uid, title, url, report, error, datetime.now(jp_tz)) )
        conn.commit()
    MAX_REPEAT = 9999
    for repeat, uid in enumerate(params.record_cache):
        if repeat >= MAX_REPEAT:
            break
        rec = api.get_record(params, uid)
        title = rec.title
        login_url = rec.login_url
        msg = "invalid Login URL"
        try:
            if login_url and not url_validator(login_url):
                put_db(uid, title, login_url, msg, 1)
                continue
        except validators.ValidationFailure:
            put_db(uid, title, login_url, msg, 1)
            continue
        try:
            login_url_parsed = urlparse(rec.login_url)
        except ValueError: #(MatchError, IndexError):
            msg = "parse error in Login URL"
            put_db(uid, title, login_url, msg, 2)
            continue
            # logger.debug( f"Login URL ({rec.login_url}) error at record uid: {record_uid}" )
        else:
            # title = rec.title
            net_loc = login_url_parsed.netloc.split(':')[0]
            login_url_domain_suffix = '.'.join(tldextract.extract(login_url_parsed.netloc.split(':')[0])[1:])
            # home_url = '://'.join(base_url)
            urls_in_title = extractor.find_urls(rec.title)
            url_in_title = urls_in_title[0].lower() if urls_in_title else None # compare with URL 1st part
            if url_in_title:
                title_url_domain_suffix = '.'.join(tldextract.extract(url_in_title)[1:])
                if login_url_domain_suffix != title_url_domain_suffix:
                    msg = "domain in title does not match with login domain!"
                    put_db(uid, title, login_url, msg, 3)

    conn.close()
    exit(0) # to suppress warning of 'Exit without exit code'