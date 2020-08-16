#  _  __  
# | |/ /___ ___ _ __  ___ _ _ ®
# | ' </ -_) -_) '_ \/ -_) '_|
# |_|\_\___\___| .__/\___|_|
#              |_|            
#
# Keeper Commander 
# Contact: ops@keepersecurity.com
#
import datetime
import hashlib
import base64
import hmac
from typing import Dict, List, Tuple, Iterator, Union
import logging
from urllib import parse 
import pprint

from .subfolder import get_folder_path, find_folders, BaseFolderNode
from .error import Error, ArgumentError

logger = logging.getLogger(__file__)

def get_totp_code(url: str) -> Tuple[str, int]:
    '''Return: (TOTP-code: str, period: int)
       Raises exception at unsupported algorithm
    '''
    comp = parse.urlparse(url)
    if comp.scheme == 'otpauth':
        secret = None
        algorithm = 'SHA1'
        digits = 6
        period = 30
        for k,v in parse.parse_qsl(comp.query):
            if k == 'secret':
                secret = v
            elif k == 'algorithm':
                algorithm = v
            elif k == 'digits':
                digits = int(v)
            elif k == 'period':
                period = int(v)
        if secret:
            tm_base = int(datetime.datetime.now().timestamp())
            tm = tm_base / period
            alg = algorithm.lower()
            if alg in hashlib.__dict__:
                key = base64.b32decode(secret, casefold=True)
                msg = int(tm).to_bytes(8, byteorder='big')
                hash =  hashlib.__dict__[alg]
                hm = hmac.new(key, msg=msg, digestmod=hash)
                digest = hm.digest()
                offset = digest[-1] & 0x0f
                base = bytearray(digest[offset:offset+4])
                base[0] = base[0] & 0x7f
                code_int = int.from_bytes(base, byteorder='big')
                code = str(code_int % (10 ** digits))
                if len(code) < digits:
                    code = code.rjust(digits, '0')
                return code, period - (tm_base % period), period
            else:
                raise Error('Unsupported hash algorithm: {0}'.format(algorithm))



class Record(object):
    """Defines a user-friendly Keeper Record for display purposes"""

    def __init__(self,record_uid='',folder='',title='',login='',password='', login_url='',notes='',
    custom_fields: List[Dict[str, str]]=[], revision=''):
        self.record_uid = record_uid 
        self.folder = folder 
        self.title = title 
        self.login_url = login_url
        self.__username = login
        '''if (not self.login) and self.__login_url:
            logger.info(f"username is gotten from parsed url.")
            self.login = self.__login_url.username'''
        self.password = password 
        self.notes = notes 
        self.custom_fields = custom_fields
        self.attachments = None
        self.revision = revision
        self.unmasked_password =  None
        self.totp = None

    @property
    def login_node_url(self) -> str:
        url = self.__login_url
        if not url:
            return ''
        non_path_url = parse.urlunparse(url._replace(path=''))
        return non_path_url
        

    @property
    def login_url(self) -> str:
        return parse.urlunparse(self.__login_url) if self.__login_url else ''

    @login_url.setter
    def login_url(self, url: str):
        if not url:
            self.__login_url = None
            return
        parsed = parse.urlparse(url)
        if parsed.username:
            if not self.__username:
                logger.info(f"'login' is set from 'login_url'")
                self.__username = parsed.username
        if not parsed.scheme:
            logger.info(f"No scheme in login_url at netloc: {parsed.netloc}")
        elif parsed.scheme != 'https':
            logger.warn(f"Insecure protocol({parsed.scheme}) at netloc: {parsed.netloc}")
        if not parsed.netloc:
            logger.info(f"No 'netloc' is found.")
        if parsed.query:
            parsed = parsed._replace(query='')
            logger.info(f"Query in netloc({parsed.netloc}) is set as an empty str.")
        if parsed.fragment:
            parsed = parsed._replace(fragment='')
            logger.info(f"Fragment in netloc({parsed.netloc}) is set as an empty str.")
        if parsed.username:
            parsed = parsed._replace(username=None)
            logger.info(f"Username:{parsed.username} in netloc({parsed.netloc}) is set as None.")
        if parsed.password:
            parsed = parsed._replace(password=None)
            logger.info(f"Password in netloc({parsed.netloc}) is set as None.")
        # if parsed.hostname:
        #     logger.info(f"Hostname:{parsed.hostname} in netloc:{parsed.netloc} is found.")
        if parsed.port:
            logger.info(f"Port:{parsed.port} in netloc:{parsed.netloc} is found.")
        self.__login_url = parsed # {m: parsed[m] for m in parsed if m not in ()}
        self.__login_url = parsed # {m: parsed[m] for m in parsed if m not in ()}

    @property
    def login(self):
        return self.__username or ''
    
    @login.setter
    def login(self, new_login):
        if new_login:
            self.__username = new_login
        
    def __eq__(self, other):
        return (self.record_uid == other.record_uid  and
            self.folder == other.folder and
            self.title == other.title   and
            self.login == other.login   and
            self.password == other.password and
            self.login_url == other.login_url   and
            self.notes == other.notes   and
            self.custom_fields == other.custom_fields   and
            self.attachments == other.attachments
            )

    def load(self, data: Dict[str, str], **kwargs):

        def xstr(s):
            return str(s or '')

        self.folder = data.get('folder', '') # xstr(data['folder'])
        if 'title' in data:
            self.title = xstr(data['title'])
        # if 'secret1' in data:
        self.__username = data.get('secret1', '')
        if 'secret2' in data:
            self.password = xstr(data['secret2'])
        if 'notes' in data:
            self.notes = xstr(data['notes'])
        link =data.get('link')
        if link: # self.login_url = xstr(data['link'])
            self.login_url = link
        if 'custom' in data:
            self.custom_fields = data['custom']
        if 'revision' in kwargs:
            self.revision = kwargs['revision']
        if 'extra' in kwargs: # and kwargs['extra']:
            extra = kwargs['extra']
            self.attachments = extra.get('files')
            if 'fields' in extra:
                for field in extra['fields']:
                    if field['field_type'] == 'totp':
                        self.totp = field['data']

    def get(self,field):
        result = ''
        for c in self.custom_fields:
            if (c['name'] == field):
                result = c['value']
                break
        return result

    def set_field(self, name, value):
        found = False
        for field in self.custom_fields:
            if field['name'] == name:
                field['value'] = value
                found = True
                break
        if not found:
            self.custom_fields.append({'name': name, 'value': value})

    def remove_field(self, name):
        if self.custom_fields:
            idxs = [i for i,x in enumerate(self.custom_fields) if x['name'] == name]
            if len(idxs) == 1:
                return self.custom_fields.pop(idxs[0])

    def display(self, print=print, **kwargs):
        def format(msg, item):
            '{0:>20s}: {1:<20s}'.format(msg, item)
        print('{0:>20s}: {1:<20s}'.format('UID', self.record_uid))
        params = None
        if 'params' in kwargs:
            params = kwargs['params']
            folders = [get_folder_path(params, x) for x in find_folders(params, self.record_uid)]
            for i in range(len(folders)):
                print('{0:>21s} {1:<20s}'.format('Folder:' if i == 0 else '', folders[i]))

        if self.title: print('{0:>20s}: {1:<20s}'.format('Title',self.title))
        if self.login: print('{0:>20s}: {1:<20s}'.format('Login',self.login))
        if self.password: print('{0:>20s}: {1:<20s}'.format('Password',self.password))
        if self.login_url: print('{0:>20s}: {1:<20s}'.format('URL',self.login_url))
        if self.revision: print(f'Revision: {self.revision}')
        #print('{0:>20s}: https://keepersecurity.com/vault#detail/{1}'.format('Link',self.record_uid))
        
        if len(self.custom_fields) > 0:
            for c in self.custom_fields:
                if not 'value' in c: c['value'] = ''
                if not 'name' in c: c['name'] = ''
                print('{0:>20s}: {1:<s}'.format(c['name'], c['value']))

        if self.notes:
            lines = self.notes.split('\n')
            for i in range(len(lines)):
                print('{0:>21s} {1}'.format('Notes:' if i == 0 else '', lines[i].strip()))

        if self.attachments:
            for i in range(len(self.attachments)):
                atta = self.attachments[i]
                size = atta.get('size') or 0
                scale = 'b'
                if size > 0:
                    if size > 1000:
                        size = size / 1024
                        scale = 'Kb'
                    if size > 1000:
                        size = size / 1024
                        scale = 'Mb'
                    if size > 1000:
                        size = size / 1024
                        scale = 'Gb'
                sz = '{0:.2f}'.format(size).rstrip('0').rstrip('.')
                print('{0:>21s} {1:<20s} {2:>6s}{3:<2s} {4:>6s}: {5}'.format('Attachments:' if i == 0 else '', atta.get('name'), sz, scale, 'ID', atta.get('id')))

        if self.totp:
            code, remain, _ = get_totp_code(self.totp)
            if code: print('{0:>20s}: {1:<20s} valid for {2} sec'.format('Two Factor Code', code, remain))

        if params is not None:
            if self.record_uid in params.record_cache:
                rec = params.record_cache[self.record_uid]
                if 'shares' in rec:
                    no = 0
                    if 'user_permissions' in rec['shares']:
                        perm = rec['shares']['user_permissions'].copy()
                        perm.sort(key=lambda r: (' 1' if r.get('owner') else ' 2' if r.get('editable') else ' 3' if r.get('sharable') else '') + r.get('username'))
                        for uo in perm:
                            flags = ''
                            if uo.get('owner'):
                                flags = 'Owner'
                            elif uo.get('awaiting_approval'):
                                flags = 'Awaiting Approval'
                            else:
                                if uo.get('editable'):
                                    flags = 'Edit'
                                if uo.get('sharable'):
                                    if flags:
                                        flags = flags + ', '
                                    flags = flags + 'Share'
                            if not flags:
                                flags = 'View'

                            print('{0:>21s} {1} ({2}) {3}'.format('Shared Users:' if no == 0 else '', uo['username'], flags, 'self' if uo['username'] == params.user else ''))
                            no = no + 1
                    no = 0
                    if 'shared_folder_permissions' in rec['shares']:
                        for sfo in rec['shares']['shared_folder_permissions']:
                            flags = ''
                            if sfo.get('editable'):
                                flags = 'Edit'
                            if sfo.get('reshareable'):
                                if flags:
                                    flags = flags + ', '
                                flags = flags + 'Share'
                            if not flags:
                                flags = 'View'
                            sf_uid = sfo['shared_folder_uid']
                            for f_uid in find_folders(params, self.record_uid):
                                if f_uid in params.subfolder_cache:
                                    fol = params.folder_cache[f_uid]
                                    if fol.type in {BaseFolderNode.SharedFolderType, BaseFolderNode.SharedFolderFolderType}:
                                        sfid = fol.uid if fol.type == BaseFolderNode.SharedFolderType else fol.shared_folder_uid
                                        if sf_uid == sfid:
                                            print('{0:>21s} {1:<20s}'.format('Shared Folders:' if no == 0 else '', fol.name))
                                            no = no + 1

        print('')

    def mask_password(self):
        if self.password != '******':
            self.unmasked_password = self.password
        self.password = '******'

    def to_string(self):
        return '\t'.join((str(self.record_uid),
            str(self.folder),
            str(self.title),
            str(self.login),
            str(self.password),
            str(self.revision),
            str(self.notes),
            str(self.login_url),
            str(self.custom_fields)))

    def to_lowerstring(self):
        return self.to_string().lower()

    def to_tab_delimited(self):

        def tabulate(*args):
            return '\t'.join(args)

        custom_fields = ''
        if self.custom_fields:
            for field in self.custom_fields:
                if ('name' in field) and ('value' in field):
                    custom_fields = '\t'.join([field['name'] + '\t' + \
                        field['value'] for field in self.custom_fields])

        return tabulate(self.folder, self.title, self.login,
                        self.password, self.login_url, self.revision, self.notes.replace('\n', '\\\\n'),
                        custom_fields)

    FIELD_KEYS = (
            'uid',
            'folder',
            'title',
            'username',
            'password',
            'web_address',
            'revision',
            'notes',
            'custom_fields'
    )

    def to_dictionary(self) -> Dict[str, Union[str, Dict[str, str]]]:
        return  {
            'uid': self.record_uid,
            'folder': self.folder,
            'title': self.title,
            'username': self.login,
            'password': self.password,
            'web_address': self.login_url,
            'revision': self.revision,
            'notes': self.notes,
            'custom_fields': self.custom_fields
        }
    
    def field_keys(self) -> Iterator[str]:
        return self.to_dictionary().keys()
    
    def field_values(self) -> Iterator[Union[str, Dict[str, str]]]:
        return self.to_dictionary().values()
    
    def field_values_str(self) -> Iterator[str]:
        for f in self.field_values():
            if isinstance(f, str):
                yield f
            else: # f is dict
                ff = (f"{n} => {c}" for n, c in f)
                yield '\t'.join(ff)
    
    def __iter__(self): # -> Iterator[Tuple[str, str], ..., Dict[str, str]]:
        '''iterates ((field_name, field), ..., {custom_filed_name: field})
        '''
        for k, v in self.to_dictionary().items():
                yield (k, v)

    def fields(self): # -> Iterator[Tuple[str, str], ..., Dict[str, str]]:
        return ((k, v) for k, v in self.__iter__()) # to_dictionary().items())
