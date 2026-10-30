from __future__ import annotations
from http.client import HTTPConnection
from pathlib import Path
import json
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from ephemeral_db import create_fixture


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
            with sqlite3.connect(db) as con:
                with self.assertRaises(sqlite3.IntegrityError):
                    con.execute('INSERT INTO demo_accounts(email,display_name) VALUES(?,?)',('seed@example.test','Duplicate'))


if __name__=='__main__':unittest.main()
