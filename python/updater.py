from datetime import date
from data_handler import append_db, build_user_timeseries_db, update_xbt_timeseries
from bitmex_api_wrapper import get_leaderboard_data
import json

def update_leaderboards():

    notional_data = get_leaderboard_data('notional')
    roe_data = get_leaderboard_data('ROE')

    append_db('notional', str(date.today()), json.dumps(notional_data))
    append_db('ROE', str(date.today()), json.dumps(roe_data))
    print('Updated @ {}'.format(date.today()))


update_leaderboards()
update_xbt_timeseries()
build_user_timeseries_db('notional')