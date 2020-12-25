# Show all UIDs and records in Vault
# set PYTHONPATH=<absolute path to keepercommander> AWS: /home/ec2-user/environment/Commander:/home/ec2-user/environment/.venv/lib/python3.6/dist-packages
import sys
import os
import getpass
import json
import datetime
import logging
import tempfile
import getpass
import urllib
import tempfile
import fnmatch
import json
from pathlib import Path
from wsgiref.simple_server import make_server
from typing import Iterable, Optional
import json2html
import pylogrus
logging.setLoggerClass(pylogrus.PyLogrus)
from ycommander import params, api, error, session, record, commands
from ycommander.commands import record as record_command
from ycommander.tsrecord import Uid
# RecordDownloadAttachmentCommand #register_commands as record_commands
    
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

ENCODING = 'utf8'

def open_session(user: str = '') -> session.KeeperSession:
    user = user or input('User:')
    password = getpass.getpass('Password:')
    prm = None
    while not prm:
        try:
            prm = params.KeeperParams(user=user, password=password)
        except error.CommunicationError:
            print(f"Wrong: {user} and password.")
            user = input('Re-input user:')
            password = getpass.getpass('Re-input password:')

    return session.KeeperSession(prm) 


def list_all_records(ss: session.KeeperSession = None, user: str = ''):
    if not ss:
        ss = open_session(user)
    for uid in ss.get_every_uid():
        yield ss[uid] #  func(rv)

def webview(webport=8080, *args):
    try:
        if is_port_in_use(webport): 
            logging.error("Port %s is in use." % webport)
            raise ValueError("Port is in use.")
        port = webport
        def app(env, start_resp):
            start_resp("200 OK",
                [("Content-type", f'text/html; charset={ENCODING}')])
            text = (s for s in args) #  tabulate(oldtable, headers=oldheaders, tablefmt='html').encode('utf-8')
            head = '<!DOCTYPE html> <html> <head> <meta charset="utf-8"/> </head>'
            body = "<body>" # <pre> <code>"
            tail = "</body> </html>" # </code> </pre>
            return [(s + '\n').encode(ENCODING) for s in (head, body, *text, tail)]
        httpd = make_server('', port, app)
        try:
            logger.info(f'A web view is opened at port {port}; Open browser with address "localhost:{port}" or cntrl-c to quit.')
            httpd.handle_request() # serve_forever()
        except KeyboardInterrupt:
            logger.info('Quit http server with Keyboard Interrupt')
    except ValueError:
        logger.info('%s is not for port number' % webview)
    except OSError as e:
        logger.error("Making web server failed by " + e.strerror)

def is_port_in_use(port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


from contextlib import contextmanager

@contextmanager
def pushd(new_dir: Path):
    old_dir = os.getcwd()
    if not new_dir.exists():
        new_dir.mkdir()
    os.chdir(str(new_dir.resolve()))
    try:
        yield Path(os.getcwd())
    finally:
        os.chdir(old_dir)

class ChangeDirDownloadAttachmentCommand(record_command.RecordDownloadAttachmentCommand):
    def __init__(self, prm: params.KeeperParams, pth :Optional[Path] = None):
        self.prm = prm
        self.old_dir = os.getcwd()
        self.pth = pth or Path(self.old_dir)
        super().__init__()

    def execute(self, uid: Uid) -> Iterable[Path]:
        files = []
        with pushd(Path(str(uid))):
            files = super().execute(self.prm, record=str(uid))
        return [self.pth / f for f in files]


def img_tag(pth: Path) -> str:
    '''src=URI-escaped fullpath without heading 'file://'
    '''
    return '<img src="' + pth.as_uri()[len('file://'):] + '" />'

def fnmatch_any(ss: Iterable[str], pat: str) -> bool:
    for s in ss:
        if fnmatch.fnmatch(s, pat):
            return True
    return False

if __name__ == '__main__':
    # webview('This is a test of webview.', 8080)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--user')
    parser.add_argument('--port')
    parser.add_argument('--with-attachment') # , action="store_true")
    args = parser.parse_args()
    try:
        webport = int(args.port)
    except (ValueError, TypeError):
        try:
            webport = int(os.environ['WEBVIEW_PORT'])
        except ValueError:
            webport = 8080
    sss = open_session(user=args.user)
    with tempfile.TemporaryDirectory('_$$$_') as tmpdir:
        with pushd(Path(tmpdir)):
            for rec in list_all_records(sss):
                if args.with_attachment:
                    if not rec.attachments:
                        continue
                    elif not fnmatch_any([att['title'] for att in rec.attachments], args.with_attachment):
                        continue
                with pushd(Path(tmpdir) / rec.record_uid) as curdir:
                    download_attachments_command = record_command.RecordDownloadAttachmentCommand()
                    recdict = rec.to_dict()
                    recdict['last_modified_time'] = rec.timestamp.date.isoformat(timespec='minutes')
                    del recdict['timestamp']
                    uid_path = Path(rec.record_uid)
                    downloaded_files = download_attachments_command.execute(sss.params, record=rec.record_uid)
                    json_rec = json.dumps(recdict)
                    html_rec = json2html.json2html.convert(json_rec)
                    webview(webport, html_rec, *(img_tag(curdir / f) for f in downloaded_files))
