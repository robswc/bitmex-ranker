import requests
import pandas as pd
import datetime
import json

current_date = datetime.datetime.now().strftime('%Y-%m-%d')

def get_leaderboard(method):
    response = requests.get('https://www.bitmex.com/api/v1/leaderboard?method={}'.format(method)).text
    print('Reponse:', '\n', response)
    return json.loads(response)

def save_leaderboard(method, file_type):
    with open('leaderboards/{}-leaderboard-{}.json'.format(method, current_date), 'w', encoding='utf-8') as f:
        json.dump(get_leaderboard(method), f, ensure_ascii=False, indent=4)


def add_current_board(method):
    data = pd.DataFrame(get_leaderboard(method))

save_leaderboard('ROE', 'json')
save_leaderboard('notional', 'json')



