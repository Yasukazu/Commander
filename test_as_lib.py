import keepercommander
config = { "user": "yskz@tutanota.de" }
from keepercommander.params import KeeperParams
params = KeeperParams(config=config)
from keepercommander import __pwd__
params.password = __pwd__
from keepercommander.api import login
#from keepercommander.commands.utils import LoginCommand
#login_command = LoginCommand()
#login_command.execute_args(params, '')
login(params)
token = input('Input Config JSON:')
print('')