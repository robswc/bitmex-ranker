import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import json
import sqlite3
from datetime import datetime
from matplotlib import style
style.use('fivethirtyeight')


# Connect to sqlite database
conn = sqlite3.connect('leaderboard.db', check_same_thread=False)
# Set cursor
c = conn.cursor()

def generate_list(users, method, datestamp):
    c.execute('SELECT * FROM {} WHERE datestamp="{}"'.format(method, datestamp))
    print('RESPONSE:')
    for row in c.fetchall():
        json_row = json.loads(row[1])
        names = [i.get('name') for i in json_row]
    if users == 'top 10':
        print('Getting Top 10')
        return names[:10]
    if users == 'top 25':
        print('Getting Top 25')
        return names
    else:
        print('Getting', str(users))
        return [str(users)]

def error(error_type):
    e_prefix = 'ERROR:'
    if error_type == 'not found':
        print(e_prefix, 'User not found in range.')


def graph_curve(user, method, from_date, to_date):
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
        dates.append(row[0])

    # Return dates and values (x, y)
    return dates, values

def graph_users(user_list, method, from_date, to_date):

    for user in user_list:
        user_graph = graph_curve(user, method, from_date, to_date)
        print(user_graph)
        plt.plot_date(user_graph[0], user_graph[1], '-')
    plt.legend(user_list)
    plt.show()

def graph_user(user, method, from_date, to_date):
    user_graph = graph_curve(user, method, from_date, to_date)
    plt.plot(user_graph[0], user_graph[1], '-')
    plt.legend([user])
    plt.show()



# graph_curve('Heavy-Autum-Wolf', 'notional', '2019-09-01', '2019-09-15')
if __name__ == '__main__':
    graph_users(generate_list('Jade-Platinum-Legs', 'notional', '2019-09-10'), 'notional', '2019-09-01', '2019-09-20')