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
# from bs4 import BeautifulSoup
from urllib import request, error
import re


class MatchError(Exception):
    pass

def extract_base(url):
    http_re = r"(http|https):\/\/([^\/]+)"
    pg = re.compile(http_re)
    rt = pg.match(url)
    if not rt:
        raise MatchError
    return rt.group(1, 2)

from html.parser import HTMLParser

class TitleParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.flag = False
        self.title = ''

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.flag = True

    def handle_data(self, data):
        if self.flag:
            self.title = data

if __name__ == '__main__':
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
                    parser = TitleParser()
                    try:
                        response = request.urlopen(home_url)
                        parser.feed(response) # soup = BeautifulSoup(response, features="html.parser")
                        page_title = parser.title # soup.title.text
                        response.close()
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
                    except Exception:
                        logger.exception("unknown error")
    logging.shutdown()
