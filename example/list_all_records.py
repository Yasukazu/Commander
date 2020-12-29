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
import argparse
from pathlib import Path
from wsgiref.simple_server import make_server
from typing import Iterable, Optional, Union, Iterator, Dict
from io import BytesIO
import base64
from datetime import datetime
import zipfile
import shutil
import pprint

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
            password = getpass.getpass(f'Re-input password for {user}:')

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

    def execute(self, uid: str) -> Iterable[Path]:
        with pushd(Path(uid)) as curdir:
            files = super().execute(self.prm, record=uid)
            return [curdir / f for f in files]


def img_tag(pth: Path) -> str:
    '''src=URI-escaped fullpath without heading 'file://'
    '''
    return '<img src="' + pth.as_uri()[len('file://'):] + '" />'

def fnmatch_any(ss: Iterable[str], pat: str) -> bool:
    for s in ss:
        if fnmatch.fnmatch(s, pat):
            return True
    return False

MAX_IMAGE_SIZE = 1000_000_000
THUMBNAIL_SIZE = (512, 512) #  width, height

def file_to_image_url(file_info: Dict[str, str], image_path: Path, size=THUMBNAIL_SIZE) -> str:
    data_type = file_info['type']
    if data_type == 'application/pdf':
        with image_path.open('rb') as fi:
            bdata = fi.read()
        data = base64.b64encode(bdata).decode('ascii')
        html = f'<embed type="{data_type}" src="data:{data_type};base64,{data}" />'
        return html
    if int(file_info['size']) > MAX_IMAGE_SIZE:
        from PIL import Image
        try:
            img = Image.open(image_path.absolute())
            img.thumbnail(size)
            tmp = BytesIO()
            data_type = 'image/png'
            img.save(tmp, format='png')
            bdata = tmp.getvalue()
        except PIL.UnidentifiedImageError:
            logger.warn(f"{file_info['name']} is not supported by PIL.")
            raise ValueError('Unsupported file type.')
    else:
        with image_path.open('rb') as fi:
            bdata = fi.read()
    return f'<img src="data:{data_type};base64,' + base64.b64encode(bdata).decode('ascii') +  '" />' #  f'" width="{size[0]}" height="{size[1]}" />'

def image_bitmap_html(data, size=THUMBNAIL_SIZE) -> str:
    encoded = base64.b64encode(data) 
    return '<img src="data:image/bmp;base64,' + encoded.decode('ascii') + f'" width="{size[0]}" height="{size[1]}" />'

INSERTMARK = 'INSERTMARK'

ZIPFILE_PREFIX = 'keeper'
ZIPFILE_EXT = 'zip'
JSONFILE_EXT = 'json'
TMPDIR_EXT = '$_$'

def main(args: argparse.Namespace):
    create_archive = args.zipfile
    try:
        webport = args.port
    except (ValueError, TypeError):
        try:
            webport = int(os.environ['WEBVIEW_PORT'])
        except ValueError:
            webport = 0
    sss = open_session(user=args.user)
    # archive = zipfile.ZipFile(archive_name, 'w') if args.zipfile else None
    all_downloaded_files = []
    with tempfile.TemporaryDirectory('.' + TMPDIR_EXT) as tmpdir:
        with pushd(Path(tmpdir)) as curdir:
            for rec in list_every_record(sss):
                if args.with_attachments:
                    if not rec.attachments:
                        continue
                    elif not fnmatch_any([att['title'] for att in rec.attachments], args.with_attachments):
                        continue
                # if archive and rec.attachments: #  if rec has attatchments # rec.attachments.append(INSERTMARK)
                recdict = rec.to_dict()
                recdict['last_modified_time'] = rec.timestamp.date.isoformat(timespec='minutes')
                del recdict['timestamp']
                img_url_htmls = {} # img_url_htmls = (file_to_image_url(f) for f in abspath_downloadeds)
                downloaded_files = []
                if rec.attachments:
                    download_attachments_command = ChangeDirDownloadAttachmentCommand(sss.params)
                    downloaded_files = download_attachments_command.execute(rec.record_uid)
                    for f in downloaded_files:
                        basename = os.path.basename(f)
                        att = next(a for a in recdict['attachments'] if a['name'] == basename)
                        if att['type']: # if any type like 'image/jpeg'
                            att['data'] = f"{INSERTMARK}[{basename}]"
                            try:
                                img_html = file_to_image_url(att,  f)
                                img_url_htmls[basename] = img_html
                            except ValueError:
                                logger.warn(f'{f} is not a supported image file.')
                    if create_archive:
                        '''for f in downloaded_files:
                             archive.write(str(f))'''
                        all_downloaded_files += downloaded_files
                if webport > 0:
                    json_rec = json.dumps(recdict)
                    html_rec = json2html.json2html.convert(json_rec)
                    for f in downloaded_files:
                        basename = os.path.basename(f)
                        key = f"{INSERTMARK}[{basename}]"
                        try:
                            html_rec = html_rec.replace(key, img_url_htmls[basename])
                        except KeyError:
                            pass
                    webview(webport, html_rec) #  , *img_url_htmls.values()) #  *(img_tag(curdir / f) for f in downloaded_files))                    
                for f in downloaded_files:
                    basename = os.path.basename(f)
                    att = next(a for a in recdict['attachments'] if a['name'] == basename)
                    with f.open('rb') as fi:
                        bdata = fi.read()
                    data = base64.b64encode(bdata).decode('ascii')
                    att['data'] = data #  replace 
                json_rec = json.dumps(recdict)
                print(json_rec + ',\n')
        if create_archive:
            # archive.close()
            # logger.warn(f"Archive file '{archive_name}' is created. Including: " + ','.join((f.name() for f in all_downloaded_files)))
            archive_name = '.'.join((ZIPFILE_PREFIX, datetime.now().date().isoformat()))
            arc_name = shutil.make_archive(archive_name, 'zip', tmpdir)
            logger.warn(f"Archive file '{arc_name}' is created. Including: " + pprint.pformat(
                [os.path.basename(str(f)) for f in all_downloaded_files]))

if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', help='User ID for Keeper login.')
    parser.add_argument('--port', type=int, default=0, help="Webview port address like 8080 except 0. Env val WEBVIEW_PORT")
    parser.add_argument('--with-attachments', help="extract and display as HTTP protocol.  records with attachment. Argument is ike '*.jpg' Display its thumbnail(shrinked) image if image file.")
    parser.add_argument('--zipfile', action='store_true', help=f'Flag to make an archive file of attachment files, with file name format as: {ZIPFILE_PREFIX}.yyyy-mm-dd.{ZIPFILE_EXT}')
    args = parser.parse_args()
    main(args)