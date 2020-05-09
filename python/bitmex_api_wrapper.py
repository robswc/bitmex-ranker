import requests

def get_leaderboard_data(method):
    endpoint = 'https://www.bitmex.com/api/v1/leaderboard'
    params = {'method': method}
    return requests.get(endpoint, params=params).json()
