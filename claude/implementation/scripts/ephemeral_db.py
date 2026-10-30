#!/usr/bin/env python3
"""Create a disposable SQLite fixture. Never accepts an existing or external DB URL."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import uuid

ROOT=Path(__file__).resolve().parents[1]


def create_fixture(directory: Path):
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    target=directory/('qa-'+uuid.uuid4().hex+'.sqlite3')
    connection=sqlite3.connect(target)
    try:
        connection.executescript('''
            CREATE TABLE metadata (name TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE demo_accounts (id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE, display_name TEXT NOT NULL);
            INSERT INTO metadata (name,value) VALUES ('environment','ephemeral-test');
            INSERT INTO demo_accounts (email,display_name) VALUES ('seed@example.test','Seeded Test User');
        ''')
        connection.commit()
    finally:connection.close()
    os.chmod(target,0o600)
    return target


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output-dir',default=str(ROOT/'.avrl'/'tmp'))
    args=p.parse_args()
    directory=Path(args.output_dir).resolve()
    allowed=(ROOT/'.avrl'/'tmp').resolve()
    if directory!=allowed:raise SystemExit('Safety: DB location must be .avrl/tmp')
    path=create_fixture(directory)
    print(json.dumps({'path':str(path),'environment':'ephemeral-test'}))


if __name__=='__main__':main()
