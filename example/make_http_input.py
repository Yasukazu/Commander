from wsgiref.simple_server import make_server
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

def is_port_in_use(port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def web_input(server: str, port: int) -> Optional[Dict[str, str]]:
    if is_port_in_use(port):
        logging.warning("Port %s is in use." % port)
        return
    out_env = ''
    try:
        text = '''<form action="/show" method="POST">
        ID: <input name="id" type="text" />
        <input value="input 2FA code" type="submit" />
        </form>'''

        def input_page(environ, start_resp):
            nonlocal out_env
            start_resp("200 OK",
                [("Content-type", 'text/html; charset=utf-8')])
            head = b'<!DOCTYPE html> <html> <head> <meta charset="utf-8"/> </head>'
            body = b"<body>" # <pre> <code>"
            tail = b"</body> </html>" # </code> </pre>
            out_env = environ
            return [head, body, text.encode('utf-8'), tail]
        httpd = make_server(server, port, input_page)
        try:
            logging.info(f'A web view is opened at port {port}; Open browser with address "localhost:{port}" or cntrl-c to quit.')
            httpd.handle_request()
        except KeyboardInterrupt:
            logging.info('Quit http server with Keyboard Interrupt')
    except ValueError:
        logging.info('%s is not for port number' % webview)
    except OSError as e:
        logging.error("Making web server failed by " + e.strerror)

    import cgi

    wsgi_input = out_env["wsgi.input"]
    form = cgi.FieldStorage(fp=wsgi_input, environ=out_env, keep_blank_values=True)
    return {k: form[k].value for k in form}

if __name__ == '__main__':
    input_data = web_input('localhost', 5557)
    print(input_data)