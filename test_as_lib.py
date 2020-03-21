import sys
import keepercommander as kc
from keepercommander import api, params
import tldextract
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
    
for record_uid in params.record_cache:
    rec = api.get_record(params, record_uid)  
    try:
        base_url = extract_base(rec.login_url) # tld = tldextract.extract(url)        
    except (MatchError, IndexError):
        base_url = ('', '')
    title = rec.title
    home_url = '://'.join(base_url)
    if title == base_url[1]:
        try:
            response = request.urlopen(home_url)
            soup = BeautifulSoup(response, features="html.parser")
            page_title = soup.title.text
            response.close()
        except error.HTTPError as err:
            page_title = ">>>> Page is Not Found <<<<"
        except AttributeError as err:
            page_title = ">>>> Title is Not Found <<<<"
        except Exception as err:
            page_title = ">>>> Login URL is unaccessable <<<<"
        print(f"{record_uid}\t{page_title}\t{home_url}") # title is just a part of login_url

