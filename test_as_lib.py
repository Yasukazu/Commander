import sys
import keepercommander as kc
from keepercommander import api, params
import tldextract
from bs4 import BeautifulSoup
from urllib import request

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
for record_uid in params.record_cache:
    rec = api.get_record(params, record_uid)
    url = rec.login_url
    tld = tldextract.extract(url)
    title = rec.title
    if title == '.'.join(tld[1:]):
        response = request.urlopen(url)
        soup = BeautifulSoup(response)
        response.close()
        tld3 = '.'.join(tld)
        print(f"{record_uid}\t{title}\t{tld3}") # title is just a part of login_url