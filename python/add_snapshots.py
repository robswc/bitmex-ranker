import os
import json
import sqlite3
from pathlib import Path

# Connect to sqlite database
conn = sqlite3.connect('leaderboard.db')
# Set cursor
c = conn.cursor()

def create_tables():
    c.execute('CREATE TABLE IF NOT EXISTS notional(datestamp TEXT, value TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS ROE(datestamp TEXT, value TEXT)')


def add_snapshots():
    # Set working directory to leaderboards folder.
    os.chdir(str('leaderboards'))
    # set leaderboards to list containing directory of all boards.
    leaderboards = [pth for pth in Path.cwd().iterdir() if pth.suffix == '.json']
    os.chdir(str('../'))

    # Create tables if not already created.
    create_tables()
    # Loop leaderboards, check if notional or ROE
    for board in leaderboards:
        with open(str(board)) as f:
            data = f.read()
            datestamp = str(board)[-15:-5]
            print('Adding...', '\n', datestamp, '\n', data)
            if "notional" in str(board):
                c.execute('INSERT INTO notional (datestamp, value) VALUES (?, ?)', (datestamp, data))
                conn.commit()
            if 'ROE' in str(board):
                c.execute('INSERT INTO ROE (datestamp, value) VALUES (?, ?)', (datestamp, data))
                conn.commit()


add_snapshots()


