import sys
import keepercommander as kc
from keepercommander import api, params

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
token = api.login(params)
for record_uid in params.record_cache:
    rec = api.get_record(params, record_uid)
    print(rec)