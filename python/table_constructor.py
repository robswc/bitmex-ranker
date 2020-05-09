import dash
import dash_html_components as html
import dash_core_components as dcc

from user_constructor import get_ranks_range, UserHandler


def get_pnl_week():
    pass


def get_pnl_day(data):
    pnl = []
    pnl.append(round((data.get('profit')[-2] - data.get('profit')[-1]) / 100000000, 2))
    pnl.append(round((data.get('usd_profit')[-2] - data.get('usd_profit')[-1]) / 100000000, 2))

    if pnl[0] != 0:
        if pnl[0] > 0:
            pnl_icon = '▲'
            pnl_icon_class = 'pnl-up-icon'
        if pnl[0] < 0:
            pnl_icon = '▼'
            pnl_icon_class = 'pnl-dn-icon'
    else:
        pnl_icon = ''
        pnl_icon_class = 'pnl-flat-icon'

    return html.Abbr(
        html.Div([
            '₿ {}'.format(pnl[0]),
            html.P('{}'.format(pnl_icon), className=pnl_icon_class)
        ], className='pnl-container'), title='${}'.format(pnl[1]), className='abbr-no-underline')


def get_pnl_YTD():
    pass

class TableConstructor:
    def __init__(self):
        pass

    def generate_table_headers(self, columns):
        return_columns = []
        for i in columns:
            return_columns.append(html.Th(i))
        return html.Tr(return_columns)

    def generate_table_rows(self, users, columns):
        rows = []
        rows.append(self.generate_table_headers(columns))
        for k, user in users.items():
            row = []
            row.append(html.Td(html.P('⬤'), style={'color': user.color}))
            row.append(html.Td(user.rank))
            row.append(html.Td(html.Button('{}'.format(user.name)), id='lb-button-{}'.format(user.name).replace('.', '-')))
            row.append(html.Td(user.btc_profit))
            row.append(html.Td(user.usd_profit))
            row.append(html.Td(get_pnl_day(user.data)))
            rows.append(html.Tr(row))

        return rows

    def build_table(self, users, columns):
        return html.Table(self.generate_table_rows(users, columns), className='leaderboard-table')



# tc.build_table(user_handler.activated_users, ['Color', 'Rank', 'Name', 'Profit', 'USD Profit'])