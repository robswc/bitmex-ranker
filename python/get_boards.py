import json
import sqlite3

# Connect to sqlite database
conn = sqlite3.connect('leaderboard.db')
# Set cursor
c = conn.cursor()

def get_board_date(datestamp, method):
    # Print query, for debugging mostly.
    print('QUERY:', '\n', 'SELECT * FROM {} WHERE datestamp="{}"'.format(method, datestamp))
    c.execute('SELECT * FROM {} WHERE datestamp="{}"'.format(method, datestamp))
    print('RESPONSE:')
    for row in c.fetchall():
        print(row)


get_board_date('2019-09-05', 'notional')