from data_handler import get_all_users, get_user_equity_curve, get_latest_leaderboard, get_leaderboards, get_xbt_timeseries, get_wr
from plotly.subplots import make_subplots
from datetime import datetime
from chart_constructor import build_user_curve_fig
import pandas as pd
import plotly.graph_objects as go
import dash_html_components as html
import dash_core_components as dcc
import json
import random

# Make variables, so we only have to get leaderboard once.
most_recent_notional = get_latest_leaderboard('notional')
dates = get_leaderboards('notional')['date'].to_list()


def get_ranks(data=most_recent_notional):
    """
    Gets ranks of users.
    :param data: Leaderboard json
    :return: {user: rank}
    """
    ranks = {}
    for idx, i in enumerate(data):
        ranks.update({i.get('name'): idx + 1})
    return ranks


# Make ranks a variable, so its only run once.
ranks = get_ranks(most_recent_notional)


def get_ranks_range(start, end, data=most_recent_notional):
    """
    Get a range of ranks
    :param start: start of range
    :param end: end of range
    :param data: Leaderboard json
    :return: List of {user: rank}
    """
    return list(get_ranks(data).keys())[start:end]


def get_btc_profits(data):
    """
    Gets the total BTC profits for user.
    :param data: User timeseries.
    :return: total BTC profit
    """
    return round(data.get('profit')[-1] / 100000000, 2)


def get_usd_profits(data):
    """
    Gets total USD profits for user.
    :param data: User timeseries.
    :return: total USD profit (using 7500 as average BTC price to estimate)
    """
    return round(round((data.get('profit')[-1] / 100000000) * 7500, 2) / 1000000, 1)


def generate_color():
    """
    Generates a random color.
    :return: random hex color as string.
    """
    return "%06x" % random.randint(0, 0xFFFFFF)


class User:
    """
    Creates a User object.  User object stores information, like color, profit, wr, etc.
    Keeps this information constant across graphs and leaderboard.  Makes users easier to work with.
    """
    def __init__(self, user):
        self.data = json.loads(get_user_equity_curve(user))
        self.name = user
        self.rank = ranks.get(self.name)
        self.color = '#{}'.format(generate_color())
        self.btc_profit = get_btc_profits(self.data)
        self.usd_profit = '{}M'.format(get_usd_profits(self.data))
        self.avg_gain = 0
        self.avg_loss = 0
        self.wlr = 0
        self.wr = round(get_wr(self.data) * 100)
        self.alpha = 0

    def update_tags(self, data):
        """
        Updates tags, not used yet.
        :param data: User timeseries.
        """
        self.btc_profit = get_btc_profits(data)
        self.usd_profit = '{}M'.format(get_usd_profits(data))
        self.rank = ranks.get(self.name)

    def build_fig(self, data, start, end, graph_method, xbt_subplot):
        """
        Creates figure object for user, given parameters.
        :param data: user timeseries
        :param start: start date
        :param end: end date
        :param graph_method: notional, notional USD
        :param xbt_subplot: include XBT subplot?
        :return: Fig object.
        """

        # Set y_data based on profit type.
        if graph_method == 'notional_usd':
            y_data = data.get('usd_profit')
        else:
            y_data = data.get('profit')

        # y_data fix.
        try:
            y_data = y_data[data.get('date').index(start): data.get('date').index(end)]
        except:
            pass

        # x_data fix.
        try:
            x_data = data.get('date')[data.get('date').index(start):data.get('date').index(end)]
        except:
            x_data = data.get('date')

        if xbt_subplot:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.01)

            # Add user trace.
            fig.add_trace(
                go.Scatter(x=x_data, y=y_data, line=dict(color=self.color, width=3)), row=1, col=1)

            # Add xbt trace.
            fig.add_trace(
                go.Scatter(
                    x=get_xbt_timeseries()['timestamp'].to_list(),
                    y=get_xbt_timeseries()['close'].to_list(),
                    line=dict(color='black', width=3)
                ),
                row=2, col=1
            )

            # Give xaxis title.
            fig.update_xaxes(title_text='Date', row=2, col=1)

        # If XBT subplot == False.
        else:

            # Add user trace.
            trace = go.Scatter(x=x_data, y=y_data, line=dict(color=self.color, width=3))

            # Create fig object.
            fig = go.Figure(data=trace)

            # Add titles, info.
            fig.update_layout(
                xaxis={'title': 'Date', 'rangeslider': {'visible': False}},
                yaxis={'title': 'Profit', 'autorange': True},
            )

        # Update fig layout.
        fig.update_layout(
            xaxis_rangeslider_visible=False,
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            margin=dict(l=20, r=20, t=5, b=20),
            xaxis_range=[start, end],
        )

        # Set grid colors
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='ghostwhite')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='ghostwhite')

        # Return completed figure object.
        return fig

    def build_block(self, start, end, graph_method, xbt_subplot):
        """
        Creates "block" object, includes header and tags, with graph.
        :param start: date
        :param end: date
        :param graph_method: notional, usd, etc
        :param xbt_subplot: include xbt subplot?
        :return: Block object, header, tags, graph.
        """

        data = json.loads(get_user_equity_curve(self.name))

        header = html.Div([
            html.Div('⬤', style={'color': self.color}, className='block-tag'),
            html.Div(self.name, className='block-name'),
            html.Div('{}'.format(self.rank), className='block-rank-tag block-tag'),
            html.Div('₿ {}'.format(self.btc_profit), className='block-bitcoin-tag block-tag'),
            html.Div('$ {}'.format(self.usd_profit), className='block-usd-tag block-tag'),
            html.Div('WR {}%'.format(self.wr), className='block-wlr-tag block-tag'),
        ], className='block-header')
        return html.Div([header, dcc.Graph(figure=self.build_fig(data, start, end, graph_method, xbt_subplot))], className='block')


class UserHandler:
    """
    Handles "activating" users, will serve more purpose in the future to improve performance.
    """
    def __init__(self):
        self.activated_users = {}
        for i in get_ranks_range(0, 24):
            self.activated_users.update({i: User(i)})
        print('Activated Users:', self.activated_users)

    def top_25(self):
        top_25 = {}
        for i in get_ranks_range(0, 24):
            for k, v in self.activated_users.items():
                if k == i:
                    top_25.update({k: v})
        return top_25

    def activate_all_users(self):
        for i in get_all_users():
            try:
                self.activated_users.update({i: User(i)})
            except:
                pass




