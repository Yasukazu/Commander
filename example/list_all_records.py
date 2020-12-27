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
from typing import Iterable, Optional, Union, Iterator, Dict
from io import BytesIO
import base64
from datetime import datetime
import zipfile

import PIL
import json2html
import pylogrus

logging.setLoggerClass(pylogrus.PyLogrus)
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

from ycommander import params, api, error, session, record, commands
from ycommander.commands import record as record_command
from ycommander.tsrecord import Uid, TsRecord

ENCODING = 'utf8'

def open_session(user: str = '') -> session.KeeperSession:
    user = user or input(__name__ + ':Input User name:')
    password = getpass.getpass(f'Input Password for {user}:')
    prm = None
    while not prm:
        try:
            prm = params.KeeperParams(user=user, password=password)
        except error.CommunicationError:
            print(f"Wrong: {user} and password.")
            user = input('Re-input user:')
            password = getpass.getpass('Re-input password:')

    return session.KeeperSession(prm) 


def list_every_record(ss: session.KeeperSession = None, user: str = '') -> Iterator[TsRecord]:
    if not ss:
        ss = open_session(user)
    for uid in ss.get_every_uid():
        yield ss[uid]

def webview(webport=8080, *args):
    try:
        if is_port_in_use(webport): 
            logging.error("Port %s is in use." % webport)
            raise ValueError("Port is in use.")
        port = webport
        def app(env, start_resp):
            start_resp("200 OK",
                [("Content-type", f'text/html; charset={ENCODING}')])
            # text = (s for s in args) #  tabulate(oldtable, headers=oldheaders, tablefmt='html').encode('utf-8')
            head = '<!DOCTYPE html> <html> <head> <meta charset="utf-8"/> </head>'
            body = "<body>" # <pre> <code>"
            tail = "</body> </html>" # </code> </pre>
            return [(s + '\n').encode(ENCODING) for s in (head, body, *args, tail)]
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

THUMBNAIL_SIZE = (64, 64) #  width, height

def file_to_image_url(file_info: Dict[str, str], image_file: Union[str, Path], size=THUMBNAIL_SIZE) -> str:
    data_type = file_info['type']
    if int(file_info['size']) > 1000_000_000:
        from PIL import Image
        if type(image_file) == Path:
            image_file = str(image_file.absolute())
        try:
            img = Image.open(image_file)
            img.thumbnail(size)
            tmp = BytesIO()
            data_type = 'image/png'
            img.save(tmp, format='png')
            bdata = tmp.getvalue()
        except PIL.UnidentifiedImageError:
            logger.warn(f"{file_info['name']} is not supported by PIL.")
            raise ValueError('Unsupported file type.')
    else:
        with open(image_file, 'rb') as fi:
            bdata = fi.read()
    return f'<img src="data:{data_type};base64,' + base64.b64encode(bdata).decode('ascii') +  '" />' #  f'" width="{size[0]}" height="{size[1]}" />'

def image_bitmap_html(data, size=THUMBNAIL_SIZE) -> str:
    encoded = base64.b64encode(data) 
    return '<img src="data:image/bmp;base64,' + encoded.decode('ascii') + f'" width="{size[0]}" height="{size[1]}" />'

INSERTMARK = '<INSERTMARK>' #  : '<INSERTED>'}

ZIPFILE_PREFIX = 'keeper'
ZIPFILE_EXT = 'zip'
JSONFILE_EXT = 'json'
TMPDIR_EXT = '$_$'

if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', help='User ID for Keeper login.')
    parser.add_argument('--port', type=int, default=8080, help="Webview port address like 8080. Env val WEBVIEW_PORT")
    parser.add_argument('--with-attachment', help="extract and display as HTTP protocol.  records with attachment. Argument is ike '*.jpg' Display its thumbnail(shrinked) image if image file.")
    archive_name = '.'.join((ZIPFILE_PREFIX, datetime.now().date().isoformat(), ZIPFILE_EXT))
    parser.add_argument('--zipfile', action='store_true', help=f'Flag to make an archive file of attachment files, with file name: {archive_name}')
    args = parser.parse_args()
    try:
        webport = args.port
    except (ValueError, TypeError):
        try:
            webport = int(os.environ['WEBVIEW_PORT'])
        except ValueError:
            webport = 8080
    sss = open_session(user=args.user)
    archive = zipfile.ZipFile(archive_name, 'w') if args.zipfile else None
    all_downloaded_files = []
    with tempfile.TemporaryDirectory('.' + TMPDIR_EXT) as tmpdir:
        with pushd(Path(tmpdir)):
            for rec in list_every_record(sss):
                if args.with_attachment:
                    if not rec.attachments:
                        continue
                    elif not fnmatch_any([att['title'] for att in rec.attachments], args.with_attachment):
                        continue
                if archive and rec.attachments: #  if rec has attatchments
                    rec.attachments.append(INSERTMARK)
                img_url_htmls = [] # img_url_htmls = (file_to_image_url(f) for f in abspath_downloadeds)
                if rec.attachments:
                    with pushd(Path(tmpdir) / rec.record_uid) as curdir:
                        download_attachments_command = record_command.RecordDownloadAttachmentCommand()
                        recdict = rec.to_dict()
                        recdict['last_modified_time'] = rec.timestamp.date.isoformat(timespec='minutes')
                        del recdict['timestamp']
                        uid_path = Path(rec.record_uid)
                        downloaded_files = download_attachments_command.execute(sss.params, record=rec.record_uid)
                        # abspath_downloadeds = [(curdir / f) for f in downloaded_files]
                        for f in downloaded_files:
                            fname = ''
                            att = next(a for a in recdict['attachments'] if a['name'] == f)
                            if att['type']: # if any type like 'image/jpeg'
                                try:
                                    img_url_htmls.append(file_to_image_url(att, curdir / f))
                                except ValueError:
                                    logger.warn(f'{f} is not a supported image file.')
                        if archive:
                            for f in downloaded_files:
                                archive.write(f)
                            all_downloaded_files += downloaded_files                    
                        json_rec = json.dumps(recdict)
                        print(json_rec + ',\n')
                        html_rec = json2html.json2html.convert(json_rec)
                        webview(webport, html_rec, *img_url_htmls) #  *(img_tag(curdir / f) for f in downloaded_files))
                    
    if archive:
        archive.close()
        logger.info(f"Archive file '{archive_name}' is created. Including: " + ','.join((f for f in all_downloaded_files)))
