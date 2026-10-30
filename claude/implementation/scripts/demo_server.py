#!/usr/bin/env python3
"""Local demo application with isolated seeded database and test-only accounts."""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from contextlib import closing
import json
import signal
import threading
from pathlib import Path
import sqlite3
import sys
from urllib.parse import urlsplit

from ephemeral_db import create_fixture
ROOT=Path(__file__).resolve().parents[1]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if urlsplit(self.path).path=='/signup':
            data=(ROOT/'example_app'/'index.html').read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        elif urlsplit(self.path).path=='/health':
            self.json_out(200,{'environment':'ephemeral-test','ready':True})
        else:
            self.json_out(404,{'error':'not found'})

    def do_POST(self):
        if self.path!='/api/signup':return self.json_out(404,{'error':'not found'})
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':
            return self.json_out(415,{'error':'JSON expected'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 1<=length<=2000:return self.json_out(413,{'error':'invalid body size'})
            body=json.loads(self.rfile.read(length))
            email=body.get('email','')
            name=body.get('name','')
            if not isinstance(email,str) or not isinstance(name,str) or not (3<=len(email)<=254) or '@' not in email or not (1<=len(name)<=80):
                return self.json_out(400,{'error':'Enter a valid name and email'})
            with closing(sqlite3.connect(self.server.db_path)) as con, con:
                con.execute('INSERT INTO demo_accounts(email,display_name) VALUES(?,?)',(email,name))
            return self.json_out(201,{'message':'Account created'})
        except (json.JSONDecodeError,TypeError,ValueError):return self.json_out(400,{'error':'invalid JSON'})
        except sqlite3.IntegrityError:return self.json_out(409,{'error':'Email already registered'})

    def json_out(self,status,payload):
        blob=json.dumps(payload).encode()
        self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(blob)))
        self.end_headers();self.wfile.write(blob)

    def log_message(self,*args):pass


def main():
    port=int(sys.argv[1]) if len(sys.argv)>1 else 8765
    if not 1024<=port<=65535:raise SystemExit('Invalid port')
    db=create_fixture(ROOT/'.avrl'/'tmp')
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.db_path=str(db)
    def terminate(_signal,_frame):
        threading.Thread(target=server.shutdown,daemon=True).start()
    signal.signal(signal.SIGTERM,terminate)
    try:
        print('TEST_SERVER',port,'EPHEMERAL',db,flush=True)
        server.serve_forever(poll_interval=.2)
    finally:
        server.server_close()
        db.unlink(missing_ok=True)


if __name__=='__main__':main()
