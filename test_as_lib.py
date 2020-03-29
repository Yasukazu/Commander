import logging
# logger.basicConfig(filename=f"{__name__}.log")
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler(f"{__file__}.log"))
import sys
import keepercommander as kc
from keepercommander import api, params
from bs4 import BeautifulSoup
from urllib import request, error
import re

try:
    user = sys.argv[1] 
except IndexError:
    user = input("User:")
try:
    password = sys.argv[2] 
except IndexError:
    from getpass import getpass
    password = getpass()
# config = {'user': user, 'password': password}
params = params.KeeperParams() # config=config)
params.user = user
params.password = password
session_token = api.login(params)
class MatchError(Exception):
    pass

def extract_base(url):
    http_re = r"(http|https):\/\/([^\/]+)"
    pg = re.compile(http_re)
    rt = pg.match(url)
    if not rt:
        raise MatchError
    return rt.group(1, 2)
    
with open(f"{__file__}.output", mode='w') as o_f:
    for record_uid in params.record_cache:
        rec = api.get_record(params, record_uid)  
        try:
            base_url = extract_base(rec.login_url)
        except (MatchError, IndexError):
            logger.error(f"Login URL ({rec.login_url}) error at record uid: {record_uid}") # base_url = ('', '')
        else:
            title = rec.title
            home_url = '://'.join(base_url)
            if title == base_url[1]:
                try:
                    response = request.urlopen(home_url)
                    soup = BeautifulSoup(response, features="html.parser")
                    rec.title = page_title = soup.title.text
                    response.close()
                    print(f"{record_uid}\t{page_title}\t{rec.login_url}", file=o_f)
                    params.sync_data = True
                    api.update_record(params, rec)
                    logger.info(f"Title of {record_uid} is update to {page_title}")
                except error.HTTPError as err:
                    logger.error(f">>>> Web page protocol error: {str(err)}:{err.code} <<<<")
                except AttributeError as err:
                    logger.error(f">>>> Title error: {str(err)} <<<<")
                except error.URLError as err:
                    logger.error(f">>>> Login web address access error: {str(err)} <<<<")
