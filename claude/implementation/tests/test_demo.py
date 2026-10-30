from __future__ import annotations
from http.client import HTTPConnection
from contextlib import closing
from pathlib import Path
import json
import threading
from http.server import ThreadingHTTPServer
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from ephemeral_db import create_fixture
from demo_server import Handler


class FixtureTests(unittest.TestCase):
    def test_seeded_disposable_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=create_fixture(Path(tmp))
            con=sqlite3.connect(db)
            self.assertEqual(con.execute('SELECT value FROM metadata WHERE name=?',('environment',)).fetchone()[0],'ephemeral-test')
            self.assertEqual(con.execute('SELECT count(*) FROM demo_accounts').fetchone()[0],1)
            con.close()

    def test_duplicate_email_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=create_fixture(Path(tmp))
            with closing(sqlite3.connect(db)) as con, con:
                with self.assertRaises(sqlite3.IntegrityError):
                    con.execute('INSERT INTO demo_accounts(email,display_name) VALUES(?,?)',('seed@example.test','Duplicate'))



class LocalHttpContractTests(unittest.TestCase):
    def test_signup_http_persistence_validation_duplicate_and_unknown_route(self):
        with tempfile.TemporaryDirectory() as temp:
            database=create_fixture(Path(temp))
            server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
            server.db_path=str(database)
            thread=threading.Thread(target=server.serve_forever,daemon=True)
            thread.start()
            try:
                client=HTTPConnection('127.0.0.1',server.server_port,timeout=3)
                def post(data):
                    client.request('POST','/api/signup',body=json.dumps(data),headers={'Content-Type':'application/json'})
                    response=client.getresponse();status=response.status
                    result=json.loads(response.read());return status,result
                self.assertEqual(post({'name':'Dana','email':'dana@example.test'})[0],201)
                self.assertEqual(post({'name':'Dana','email':'dana@example.test'})[0],409)
                self.assertEqual(post({'name':'','email':'bad'})[0],400)
                client.request('GET','/.git/config')
                response=client.getresponse();self.assertEqual(response.status,404);response.read()
                with closing(sqlite3.connect(database)) as con:
                    self.assertEqual(con.execute("SELECT count(*) FROM demo_accounts WHERE email='dana@example.test'").fetchone()[0],1)
                client.close()
            finally:
                server.shutdown();server.server_close();thread.join(timeout=3)

if __name__=='__main__':unittest.main()
