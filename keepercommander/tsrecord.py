from urllib import parse
from functools import cached_property
from typing import NamedTuple, Optional
from datetime import datetime
from .record import Record


class Uid(bytes):
    pass


class Timestamp(float):
    def dt(self):
        return  datetime.fromtimestamp(self)


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
        return Uid(self.record_uid, encoding='ascii')

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


"""
@login_url.setter
def login_url(self, url: str):
    if not url:
        self.login_url = ''
        return
    parsed = parse.urlparse(url)
    if parsed.username:
        if not self.__username:
            logger.info(f"'login' is set from 'login_url'")
            self.__username = parsed.username
    if not parsed.scheme:
        logger.info(f"No scheme in login_url at netloc: {parsed.netloc}")
    elif parsed.scheme != 'https':
        logger.warning(f"Insecure protocol({parsed.scheme}) at netloc: {parsed.netloc}")
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
    self.__login_url = parsed  # {m: parsed[m] for m in parsed if m not in ()}
    """
