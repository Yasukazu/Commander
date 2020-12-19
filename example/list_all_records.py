# Show all UIDs and records in Vault
# set PYTHONPATH=<absolute path to keepercommander> AWS: /home/ec2-user/environment/Commander:/home/ec2-user/environment/.venv/lib/python3.6/dist-packages
import sys
import os
import getpass
import json
import datetime
import logging
import tempfile
from wsgiref.simple_server import make_server

import pylogrus
logging.setLoggerClass(pylogrus.PyLogrus)
from ycommander import params, api, record, error, session

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

ENCODING = 'utf8'

def list_all_records(user: str, password: str):
    prm = params.KeeperParams(user=user, password=password)
    ss = session.KeeperSession(prm) 
    for uid in ss.get_every_uid():
        yield ss[uid] #  func(rv)

def webview(s, webport=8080):
    try:
        if is_port_in_use(webport): 
            logging.error("Port %s is in use." % webport)
            raise ValueError("Port is in use.")
        port = webport
        def app(env, start_resp):
            start_resp("200 OK",
                [("Content-type", 'text/html; charset=utf-8')])
            text = s.encode(ENCODING) #  tabulate(oldtable, headers=oldheaders, tablefmt='html').encode('utf-8')
            head = b'<!DOCTYPE html> <html> <head> <meta charset="utf-8"/> </head>'
            body = b"<body>" # <pre> <code>"
            tail = b"</body> </html>" # </code> </pre>
            return [head, body, text, tail]
        httpd = make_server('', port, app)
        try:
            logger.info(f'A web view is opened at port {port}; Open browser with address "localhost:{port}" or cntrl-c to quit.')
            httpd.handle_request()
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


if __name__ == '__main__':
    # webview('This is a test of webview.', 8080)
    try:
        webport = os.environ['WEBVIEW_PORT']
    except ValueError:
        webport = 8080
    import getpass
    import pprint
    user = input('User:')
    password = getpass.getpass('Password:')
    for rec in list_all_records(user, password):
        # with tempfile.NamedTemporaryFile('w') as tfile:
        recdict = pprint.pformat(rec.to_dict())
        webview(recdict, webport)
        #    tfile.write(recdict + '\n')
        