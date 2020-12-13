from urllib import parse
from typing import NamedTuple, Optional
import datetime
from .record import Record
import sys
if sys.version_info.minor < 8:
    from cached_property import cached_property
else:
    from functools import cached_property

class Uid(bytes):
    '''byte type used for uid'''

    ENCODING = 'ascii'

    @classmethod
    def new(cls, c: str):
        return Uid(c.encode(Uid.ENCODING))

    def __str__(self):
        return self.decode(Uid.ENCODING)


class Timestamp(float):
    @property
    def date(self):
        return datetime.datetime.fromtimestamp(self / 1000)


class TsRecord(Record):
    def __init__(self, rec: Record, timestamp: Optional[Timestamp] = None):
        super().__init__()
        self.timestamp: Timestamp = timestamp
        self.record_uid = rec.record_uid
        self.folder = rec.folder
        self.title = rec.title
        self.login_url = rec.login_url
        self.login = rec.login
        self.password = rec.password
        self.notes = rec.notes
        self.custom_fields = rec.custom_fields
        self.attachments = rec.attachments
        self.revision = rec.revision
        self.unmasked_password = rec.unmasked_password
        self.totp = rec.totp

    @classmethod
    def new(cls, rec: Record, timestamp: Timestamp):
        tsr = TsRecord(rec)
        tsr.timestamp = timestamp
        return tsr

    ''' from .session import KeeperSession
    @classmethod
    def new_with_timestamp(cls, uid: Uid, ks: KeeperSession):
        rec = ks.get_record_with_timestamp()
        tsr = TsRecord(rec)
        return tsr '''

    @cached_property
    def login_url_components(self) -> NamedTuple:
        '''
        @return: (scheme, netloc, path, params, query, fragment)
        '''
        return parse.urlparse(self.login_url)

    @cached_property
    def login_node_url(self) -> str:
        urlcomp = parse.urlparse(self.login_url)
        return (urlcomp.scheme + '://' if urlcomp.scheme else '') + urlcomp.netloc

    @cached_property
    def url(self) -> str:
        urlcomp = parse.urlparse(self.login_url)  # if self.__login_url else ''
        return (urlcomp.scheme + '://' if urlcomp.scheme else '') + urlcomp.netloc + urlcomp.path

    @cached_property
    def uid(self) -> Uid:
        return Uid(self.record_uid, encoding=Uid.ENCODING)

    @cached_property
    def username(self) -> str:
        return self.login.casefold()

    def __eq__(self, other) -> bool:
        '''ignores record_uid
        '''
        return ( #  self.record_uid == other.record_uid and
                self.folder == other.folder and
                self.title == other.title and
                self.login == other.login and
                self.password == other.password and
                self.login_url == other.login_url and
                self.notes == other.notes and
                self.compare_custom_fields(other) and
                self.compare_attachments(other) and
                self.revision == other.revision and
                self.unmasked_password == other.unmasked_password and
                self.totp == other.totp
                )

    def compare_custom_fields(self, other) -> bool:
        if set(self.custom_fields.keys()) != set(other.custom_fields.keys()):
            return False
        for k in self.custom_fields.keys():
            if self.custom_fields[k] != other.custom_fields[k]:
                return False
        return True

    def compare_attachments(self, other) -> bool:
        if not self.attachments or not other.attachments:
            return False
        if set(self.attachments.keys()) != set(other.attachments.keys()):
            return False
        for k in self.attachments.keys():
            if self.attachments[k] != other.attachments[k]:
                return False
        return True

    def to_dict(self):
        return self.__dict__

