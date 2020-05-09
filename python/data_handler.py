from datetime import date, datetime
import json
import sqlalchemy as sql
import pandas as pd
from os import listdir
from os.path import isfile, join
import requests
import time

# Create SQLAlchemy connection.
engine = sql.create_engine('sqlite:///data/leaderboards.db')

# Load xbt_timeseries (so we only have to do it once!)
xbt_timeseries = pd.read_csv('data/xbt_timeseries.csv', index_col=['timestamp'])


def append_db(table, date, json_data):
    """
    Appends given json data to database.
    :param json_data: Leaderboard json data.
    :param date: Date to add leaderboard to.
    """
    # Concat existing database dataframe with new leaderboard dataframe.
    df = pd.concat([pd.read_sql_table(table, engine),
                    pd.DataFrame({'date': [date], 'leaderboard': [json_data]})])
    # Drop duplicates.
    df.drop_duplicates(subset=['date', 'leaderboard'], inplace=True, keep='last')
    df.set_index(['date'], inplace=True)
    df.sort_index(inplace=True)
    # Export dataframe to database file.
    df.to_sql(table, engine, if_exists='replace')


def add_legacy_boards():
    """
    Quick and dirty function to add old json stored boards.
    """
    files = [f for f in listdir('data/json_backup') if isfile(join('data/json_backup', f))]
    for i in files:
        if 'notional' in i:
            method = 'notional'
            cut = i[21:-5]
        if 'ROE' in i:
            method = 'ROE'
            cut = i[18:-5]
        with open('data/json_backup/{}'.format(i)) as f:
            append_db(method, cut, str(f.read()))
        print('Added board: {}'.format(i))


def get_leaderboards(method):
    """
    Gets leaderboard database table.
    :param method: Type, notional or ROE
    :return: pandas dataframe of database table.
    """
    return pd.read_sql_table(method, engine)


def get_latest_leaderboard(method):
    """
    Gets latest leaderboard json from database.
    :param method: Type, notional or ROE
    :return: json data of most recent leaderboard
    """
    return json.loads(pd.read_sql_table(method, engine).iloc[-1]['leaderboard'])


def get_leaderboards_range(method, start, end):
    get_leaderboards(method)
    pass


def get_user_equity_curve_pd(method, user):
    """
    Legacy function to create an equity curve for a specific user.
    :param method:
    :param user:
    :return: returns dict object, {user: [equity as timeseries list]}
    """
    user_profit = []
    user_dates = []
    leaderboards = get_leaderboards(method)
    for idx, row in leaderboards.iterrows():
        try:
            for i in json.loads(row['leaderboard']):
                if i.get('name') == user:
                    user_profit.append(i.get('profit'))
                    user_dates.append(row['date'])
        except:
            print('Missing data at: \n'.format(row))

    return {user: {'dates': user_dates, 'profits': user_profit}}


def get_user_equity_curve(user):
    """
    Not sure what this is... will come back to it.
    :param user:
    :return:
    """
    timeseries = pd.read_csv('data/user_timeseries.csv')
    timeseries.set_index(['user'], inplace=True)
    return timeseries.loc[user]['timeseries']


def get_xbt_price(data, date):
    """
    Gets the price of bitcoin on a specific date.
    :param data: Pandas Dataframe
    :param date: Requested Date
    :return: Bitcoin price on given date, as int.
    """
    return data.loc['{}T00:00:00.000Z'.format(date)]['close']


def get_usd_pnl(user_data):
    usd_profit = []
    prev_profit = user_data.get('profit')[0]

    for idx, date in enumerate(user_data.get('date')):
        # * get_xbt_price(xbt_timeseries, date
        usd_profit.append(
            round(((user_data.get('profit')[idx] - prev_profit) / 100000000) * get_xbt_price(xbt_timeseries, date), 2))
        prev_profit = user_data.get('profit')[idx]

    return usd_profit


def get_usd_notional(user_data):
    """
    Takes user_data json, updates dict with usd_profits. ALSO contains
    WLR calc, as this saves us from going through another loop.
    :param user_data:
    :return: List of USD profits.
    """
    usd_profit = []
    prev_profit = user_data.get('profit')[0]
    total_profit = 0
    win = 0
    loss = 0

    for idx, date in enumerate(user_data.get('date')):
        # * get_xbt_price(xbt_timeseries, date
        profit = round(((user_data.get('profit')[idx] - prev_profit) / 100000000) * get_xbt_price(xbt_timeseries, date), 2)
        prev_profit = user_data.get('profit')[idx]
        total_profit = total_profit + profit
        usd_profit.append(total_profit)

    return usd_profit


def get_wr(user_data):
    """
    Takes user data, returns winrate
    :param user_data:
    :return: List of USD profits.
    """
    prev_profit = user_data.get('profit')[0]
    win = 0
    loss = 0
    wr = 0

    for idx, date in enumerate(user_data.get('date')):
        profit = (user_data.get('profit')[idx] - prev_profit) * get_xbt_price(xbt_timeseries, date)
        prev_profit = user_data.get('profit')[idx]
        if profit > 0:
            win += 1
        if profit < 0:
            loss += 1

    try:
        wr = win / (win + loss)
    except:
        wr = 0

    return wr


def build_user_timeseries_db(method):
    """
    Creates timeseries csv from leaderboards.db.
    This allows for faster processing and easier chart creation.
    :param method: notional, ROE
    """
    leaderboards = get_leaderboards(method)
    user_data = {}
    timeseries_data = []

    # Loop each row in leaderboard table, create users and update dates/profits.
    for idx, row in leaderboards.iterrows():
        try:
            for i in json.loads(row['leaderboard']):
                user = i.get('name')
                profit = i.get('profit')
                try:
                    user_data.get(user).get('date').append(row['date'])
                    user_data.get(user).get('profit').append(profit)
                except Exception as e:
                    user_data.update({user: {'date': [], 'profit': []}})
        except Exception as e:
            print('Missing data at: \n'.format(row))

    # Create timeseries data.
    for k, v in user_data.items():
        # Add USD notional via function.
        try:
            v.update({'usd_profit': get_usd_notional(v)})
        except Exception as e:
            print('Error with adding USD notional:\n{}\n{}'.format(k, e))

        # Add user WR via function.
        try:
            v.update({'wr': get_wr(v)})
        except Exception as e:
            print('Error with adding winrate:\n{}\n{}'.format(k, e))

        # Add user daily pnl via function.
        try:
            timeseries_data.append({'user': k, 'timeseries': json.dumps(v)})
        except:
            print('Error adding timeseries:\n{}'.format(k))



    # Create timeseries Dataframe.
    timeseries_db = pd.DataFrame(timeseries_data, columns=['user', 'timeseries'])
    timeseries_db.to_csv('data/user_timeseries.csv', index=False)


def get_all_users():
    """
    Gets all users listed in the timeseries.csv database.
    :return: list of users from timeseries.
    """
    return pd.read_csv('data/user_timeseries.csv')['user'].to_list()


def get_bitmex_price_data(start, end):
    """
    Gets OHLC data from bitmex API.
    :param start:
    :param end:
    :return: json of OHLC
    """
    url = 'https://www.bitmex.com/api/v1/trade/bucketed'
    params = {'binSize': '1d', 'partial': False, 'symbol': 'XBT', 'startTime': start, 'endTime': end}
    return requests.get(url, params=params).json()


def get_bitmex_historical_data(start, end):
    """
    Temporary function, will be used to handle multiple requests.
    :param start:
    :param end:
    :return:
    """
    data = get_bitmex_price_data(start, end)
    df = pd.DataFrame(data, columns=['timestamp', 'close'])
    df.to_csv('data/{}.csv'.format(end), index=False)


def update_xbt_timeseries():
    """
    Updates the xbt timeseries csv database.
    :return:
    """
    current_price = pd.DataFrame(get_bitmex_price_data(date.today(), date.today()), columns=['timestamp', 'close'])
    historical_prices = pd.read_csv('data/xbt_timeseries.csv')
    new_prices = pd.concat([current_price, historical_prices])
    new_prices.drop_duplicates(subset=['timestamp', 'close'], inplace=True, keep='last')
    new_prices.set_index(['timestamp'], inplace=True)
    new_prices.sort_index(inplace=True)
    new_prices.to_csv('data/xbt_timeseries.csv')


def get_xbt_timeseries():
    """
    Gets xbt timeseries csv database as dataframe.
    :return: Dataframe
    """
    return pd.read_csv('data/xbt_timeseries.csv')



