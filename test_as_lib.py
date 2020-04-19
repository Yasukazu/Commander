import logging
# logger.basicConfig(filename=f"{__name__}.log")
logger = logging.getLogger(__name__)
sHandler = logging.StreamHandler()
sHandler.setLevel(logging.INFO)
logger.addHandler(sHandler)
logfilenode = __file__.rsplit('.')[0]
handler = logging.FileHandler(f"{logfilenode}.log")
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
import sys
import keepercommander as kc
from keepercommander import api, params
from bs4 import BeautifulSoup # python -m pip install bs4
import  requests
from urllib import request, error
import re
import os

class MatchError(Exception):
    pass

def extract_base(url):
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
    params = params.KeeperParams() # config=config)
    params.user = user
    params.password = password
    session_token = api.login(params)
    with open(f"{__file__}.output", mode='a') as o_f:
        for record_uid in params.record_cache:
            rec = api.get_record(params, record_uid)
            try:
                base_url = extract_base(rec.login_url)
            except (MatchError, IndexError):
                logger.debug(f"Login URL ({rec.login_url}) error at record uid: {record_uid}") # base_url = ('', '')
            else:
                title = rec.title
                home_url = '://'.join(base_url)
                if title == base_url[1]:
                    req = request.Request(home_url)
                    try:
                        with request.urlopen(req) as res:
                           body = res.read()
                        soup = BeautifulSoup(body.decode('utf-8'), features="html.parser")
                        page_title = soup.title.text
                        rec.title = page_title
                        params.sync_data = True
                        api.update_record(params, rec)
                        logger.info(f"Title of {record_uid} is update to {page_title}")
                        print(f"{record_uid}\t{page_title}\t{rec.login_url}", file=o_f)
                    except error.HTTPError as err:
                        logger.info(f">>>> Web page protocol error: {str(err)}:{err.code} <<<<")
                    except AttributeError as err:
                        logger.info(f">>>> Title error: {str(err)} <<<<")
                    except error.URLError as err:
                        logger.info(f">>>> Login web address access error: {str(err)} <<<<")
                    except Exception as ex:
                        logger.exception("unknown error at %s: " % record_uid)
                        raise
    logging.shutdown()
