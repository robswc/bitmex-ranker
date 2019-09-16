import json
import sqlite3
from datetime import datetime
from random import randint

# Connect to sqlite database
conn = sqlite3.connect('leaderboard.db')
# Set cursor
c = conn.cursor()

def get_dash_user(user, method, from_date, to_date):
    # Set dates and values to empty lists (x, y)
    dates = []
    values = []
    # Query database
    print('Graphing user: ', str(user), method, from_date, to_date)
    c.execute('SELECT * FROM {} WHERE datestamp BETWEEN "{}" AND "{}"'.format(method, from_date, to_date))
    for row in c.fetchall():
        # Convert row to json.
        json_row = json.loads(row[1])
        # Grab names from json data.
        names = [i.get('name') for i in json_row]
        # Position in leaderboard of user.
        position = names.index(user)
        # Append profit to value list, if notional divide by 1 mil, else leave as is.
        values.append(
            round((json_row[position]['profit'] / 100000000), 6)
            if method == 'notional'
            else json_row[position]['profit'])
        # Append dates list with date.
        dates.append(datetime.strptime([user_graph[0]], '%Y-%m-%d'))

    # Return dates and values (x, y)
    return dates, values

def get_usd_value(xbt, price):
    return xbt * price

def get_pnl_percent(old, new):
    return (new - old) / old * 100

def gen_rand_color():
    rand_color = str('#%02x%02x%02x') % (randint(0, 255), randint(0, 255), randint(0, 255))
    return str(rand_color)

def generate_colors(quantity):
    colors = []
    for i in range(0, quantity):
        rand_color = str('#%02x%02x%02x') % (randint(0, 255), randint(0, 255), randint(0, 255))
        colors.append(rand_color)
    return colors

