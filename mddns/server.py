import os
import json
import hmac
import binascii
import threading
import time
import itertools
import smtplib
from email.mime.text import MIMEText
from http.server import HTTPServer, BaseHTTPRequestHandler


# TODO: Tests, Logging, Configuration, Packaging, Deployment

class Handler(BaseHTTPRequestHandler):

    encoding = 'ascii'

    def do_GET(self):
        if self.authenticate_request():
            ip = self.client_address[0]
            self.server.updater.update_ip(ip)
            self.success(ip)
        else:
            self.forbidden()

    def success(self, ip):
        self.send_response(200)
        self.end_headers()
        self.json_response({
            'status': 'success',
            'message': 'IP address successfully updated',
            'ip': ip,
        })

    def forbidden(self):
        self.send_response(403)
        self.end_headers()
        self.json_response({
            'status': 'forbidden',
            'message': 'Invalid authentication token',
        })

    def json_response(self, obj):
        self.wfile.write(json.dumps(obj).encode(self.encoding))

    def authenticate_request(self):
        return self.server.updater.check_token(self.path[1:])


class Updater:
    def __init__(self, config):
        self.ip_filepath = config.get('checker', 'ip_file')
        self.token_filepath = config.get('checker', 'token_file')
        self.endpoint = config.get('server', 'public_endpoint')
        self.config = config

    def update_ip(self, ip):
        with open(self.ip_filepath, 'wb') as fh:
            fh.write(ip.encode('ascii'))
        if os.path.exists(self.token_filepath):
            os.remove(self.token_filepath)

    def is_update_needed(self):
        return not (os.path.exists(self.ip_filepath) or
                    os.path.exists(self.token_filepath))

    def trigger_update(self):
        auth_token = binascii.b2a_hex(os.urandom(32))
        with open(self.token_filepath, 'wb') as fh:
            fh.write(auth_token)
        self.sendmail(auth_token)

    def sendmail(self, token):
        addr = 'http://{}/{}'.format(self.endpoint, token.decode('ascii'))
        msg = MIMEText(
            'Click on the following link when you are connected to your home\n'
            'network to update your IP address:\n'
            '\n'
            '' + addr + '\n'
        )

        msg['Subject'] = 'Please update your IP address'
        msg['From'] = self.config.get('email', 'from_email')
        msg['To'] = self.config.get('email', 'to_email')

        print('sending email')

        s = smtplib.SMTP_SSL(self.config.get('email', 'smtp_server'))
        s.login(
            self.config.get('email', 'smtp_user'),
            self.config.get('email', 'smtp_password')
        )
        s.send_message(msg)
        s.quit()

        print('done')

    def check(self):
        if self.is_update_needed():
            self.trigger_update()

    def check_token(self, request_token):
        if not os.path.exists(self.token_filepath):
            return False
        with open(self.token_filepath, 'rb') as fh:
            token = fh.read().decode('ascii')
        return hmac.compare_digest(token, request_token)

    def start_checking(self, check_interval):
        def check():
            for i in itertools.cycle(range(check_interval)):
                if self.stop_requested:
                    break
                if not i:
                    print('Checking')
                    self.check()
                time.sleep(1)
        self.stop_requested = False
        self.checker = threading.Thread(target=check)
        self.checker.start()

    def stop_checking(self):
        self.stop_requested = True
        try:
            self.checker.join()
        except KeyboardInterrupt:
            print('Forcing exit!')


def runserver(config):
    address = (
        config.get('server', 'interface'),
        config.getint('server', 'port')
    )
    httpd = HTTPServer(address, Handler)
    httpd.updater = Updater(config)
    httpd.updater.start_checking(config.getint('checker', 'interval'))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Quitting...')
        httpd.updater.stop_checking()
