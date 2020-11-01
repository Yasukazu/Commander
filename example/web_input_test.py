# coding: utf-8
from bottle import route,run,request
from wsgiref.simple_server import make_server

class WebInput:

    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.init()
        self.data = None

    @route("/input")
    def init(self):
        return """
        <form action="/show" method="GET">
        ID: <input name="id" type="text" />
        <input value="input 2FA code" type="submit" />
        </form>
        """

    @route("/show", method="GET")
    def show(self):
        id_str = request.query.get("id")
        self.data = id_str
        return f"2FA code = {id_str}"

    def web_input(self):
        run(host=self.addr, port=self.port)

    if webview:
        try:
            if is_port_in_use(webview):
                logging.warning("Port %s is in use." % webview)
                return formatted
            port = webview
            def helo(env, start_resp):
                start_resp("200 OK",
                    [("Content-type", 'text/html; charset=utf-8')])
                text = tabulate(oldtable, headers=oldheaders, tablefmt='html').encode('utf-8')
                head = b'<!DOCTYPE html> <html> <head> <meta charset="utf-8"/> </head>'
                body = b"<body>" # <pre> <code>"
                tail = b"</body> </html>" # </code> </pre>
                return [head, body, text, tail]
            httpd = make_server('', port, helo)
            try:
                logging.info(f'A web view is opened at port {port}; Open browser with address "localhost:{port}" or cntrl-c to quit.')
                httpd.handle_request()
            except KeyboardInterrupt:
                logging.info('Quit http server with Keyboard Interrupt')
        except ValueError:
            logging.info('%s is not for port number' % webview)
        except OSError as e:
            logging.error("Making web server failed by " + e.strerror)
    return formatted