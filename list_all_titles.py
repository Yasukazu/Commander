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
#from pathlib import Path
#file_dir = os.path.dirname(__file__)
#parent_dir = os.path.join(file_dir, '..')
#sys.path.append(parent_dir)
import keepercommander as kc
from keepercommander import api, params
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
    __SQLFILE__ = "title-keeper"
    __SQLEXT__ = '.sqlite'
    TABLE_NAME = 'nomatch'
    conn = sqlite3.connect(f"{__SQLFILE__}{__SQLEXT__}",
        detect_types = sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    sqlite3.dbapi2.converters['DATETIME'] = sqlite3.dbapi2.converters['TIMESTAMP']
    cur = conn.cursor()
    cur.execute(f"CREATE TABLE if not exists {TABLE_NAME} (uid text unique, report text, error integer, updated datetime)")
    jp_tz = timezone(timedelta(hours=+9), 'JST')
    # with open(f"{__file__}.output", mode='a') as o_f:
    for record_uid in params.record_cache:
        rec = api.get_record(params, record_uid)
        login_url = rec.login_url
        msg = "invalid Login URL"
        try:
            if not url_validator(login_url):
                print(msg)
                cur.execute(f"insert into {TABLE_NAME}(uid, report, error, updated)  value (?,?,?,?)",
                    [record_uid, msg, 1, datetime.now(jp_tz)] )
                continue
        except validators.ValidationFailure:
            print(msg)
            cur.execute(f"insert into {TABLE_NAME}(uid, report, error, updated)  value (?,?,?,?)",
                [record_uid, msg, 1, datetime.now(jp_tz)] )
            continue
        try:
            parse_result = urlparse(rec.login_url)
        except ValueError: #(MatchError, IndexError):
            msg = "parse error in Login URL"
            print(msg)
            cur.execute(f"insert into {TABLE_NAME}(uid, report, error, updated)  value (?,?,?,?)",
                [record_uid, msg, 2, datetime.now(jp_tz)] )
            continue
            # logger.debug( f"Login URL ({rec.login_url}) error at record uid: {record_uid}" )
        else:
            # title = rec.title
            net_loc = parse_result.netloc.split(':')[0]
            # home_url = '://'.join(base_url)
            urls_in_title = extractor.find_urls(rec.title)
            url_in_title = urls_in_title[0] if urls_in_title else None
            if url_in_title:
                if url_in_title != not_loc:
                    msg = "URL in title does not match with login URL!"
                    print(msg)
                    cur.execute(f"insert into {TABLE_NAME}(uid, report, error, updated)  value (?,?,?,?)",
                    [record_uid, msg, 3, datetime.now(jp_tz)]
                    )
             #for url_in_title in urls_in_title: # if not title:  # if title is empty
                # print("No title at record_uid:%s" % record_uid)
                # res.encoding = res.apparent_encoding()
                # req = request.Request(home_url)
                # with request.urlopen(req) as res:
                #    body = res.read()
                '''
                try:
                    res = requests.get(home_url)
                    soup = BeautifulSoup(res.text,# body.decode('utf-8')
                                         features="html.parser") 
                    page_title = soup.title.text
                    if not page_title:
                        print("No page title in webpage:%s" % home_url)
                        continue
                    rec.title = page_title
                    params.sync_data = True
                    api.update_record(params, rec)
                    logger.info(
                        f"Title of {record_uid} is update to {page_title}")
                    print(f"{record_uid}\t{page_title}\t{rec.login_url}",
                          file=o_f)
                except error.HTTPError as err:
                    logger.info(
                        f">>>> Web page protocol error: {str(err)}:{err.code} <<<<"
                    )
                except AttributeError as err:
                    logger.info(f">>>> Title error: {str(err)} <<<<")
                except error.URLError as err:
                    logger.info(
                        f">>>> Login web address access error: {str(err)} <<<<"
                    )
                except Exception as ex:
                    logger.exception("unknown error at %s: " % record_uid)
                    raise
                    '''
    logging.shutdown()
    exit(0) # to suppress warning of 'Exit without exit code'