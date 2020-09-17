from urllib import parse
from functools import cached_property
from typing import NamedTuple, Optional
import datetime
from .record import Record
import sys
if sys.version_info.minor < 8:
    from cached_property import cached_property


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
    def __init__(self, rec: Record): #, timestamp: Timestamp):
        super().__init__()
        self.timestamp: Timestamp = Timestamp(0.0)
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
        return (self.record_uid == other.record_uid and
                self.folder == other.folder and
                self.title == other.title and
                self.login == other.login and
                self.password == other.password and
                self.login_url == other.login_url and
                self.notes == other.notes and
                self.custom_fields == other.custom_fields and
                self.attachments == other.attachments
                )

