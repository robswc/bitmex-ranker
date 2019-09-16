import dash
import dash_core_components as dcc
import dash_html_components as html
from create_equity import graph_curve, generate_list
from ranker_data import generate_colors, get_usd_value, get_pnl_percent
from datetime import datetime as dt
from datetime import timedelta
import dash_table
import time
import pandas as pd
import plotly.graph_objs as go
import requests

'''
Please keep in mind this is still very early in development!
Lots to fix, messes to clean up! But hey, it works!
'''

about_text = \
"""
Bitmex Ranker is an online application built with Dash/Python that uses the Bitmex API to track
the best traders on Bitmex.  The graphs show the gains/losses in bitcoin by the top 25 traders on bitmex.
"""

price = requests.get('https://www.bitmex.com/api/v1/orderBook/L2?symbol=XBT&depth=1').json()[1]['price']


external_css = ['https://raw.githubusercontent.com/Robswc/bitmex-ranker/master/python/dash/css/main.css',
                'https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css']

app = dash.Dash('vehicle-data', external_stylesheets=external_css)

user_data = {}





# Get Users
def fetch_users(method, users, from_date, to_date):
    print('---- Fetching Users')
    user_data.clear()
    print('user data', user_data)
    for user in users:
        user_graph = graph_curve(user, method, from_date, to_date)
        user_entry = {str(user): {'datestamp': user_graph[0], 'profit': user_graph[1]}}
        user_data.update(user_entry)
    print('user data', '\n', user_data)

fetch_users('notional',
            generate_list('top 25', 'notional', dt.today().strftime('%Y-%m-%d')),
            (dt.today() - timedelta(days=7)).strftime('%Y-%m-%d'),
            dt.today().strftime('%Y-%m-%d')
            )
colors = generate_colors(len(user_data))

# Create the leaderboard table
def build_leaderboard_table(user_data):
    table = []
    print('USER DATA', '\n', user_data)
    for i in user_data.keys():
        row = [str(i),
               '₿ {:,.2f}'.format(user_data.get(i)['profit'][-1]),
               '$ {:,.2f}'.format(get_usd_value(user_data.get(i)['profit'][-1], price)),
               '{:,.2f}'.format(user_data.get(i)['profit'][-1] - user_data.get(i)['profit'][0]),
               '{:,.2f}%'.format(get_pnl_percent(user_data.get(i)['profit'][0], user_data.get(i)['profit'][-1]))
               ]
        print(row)
        table.append(row)

    df = pd.DataFrame(table, columns=['Name', 'Bitcoin', 'USD', 'PNL', 'PNL %'])
    print('DATA FRAMEEEEE', '\n', df)
    return df

df_test = build_leaderboard_table(user_data)

app.layout = html.Div([
    html.Div([
        html.Img(src='https://github.com/Robswc/bitmex-ranker/raw/master/img/bitmex-ranker-logo.png',
                 className='bitmex-ranker-logo',
                 style={'height': '20vh', 'padding': '2%'}
                 ),
        html.A('by @robwc', className='bitmex-ranker-robswc'),
        html.A(' about', href='#about-section')
        ]),

    html.Div([
        html.H3('Parameters', className='ranker-header'),
        dcc.DatePickerRange(
            id='my-date-picker-range',
            start_date_placeholder_text="Start Period",
            end_date_placeholder_text="End Period",
            end_date=dt.now().strftime('%Y-%m-%d'),
            start_date=(dt.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
            display_format='D-M-YYYY',
            className='bitmex-ranker-daterange',
        ),
    ]),
    html.H3('Graphs', className='ranker-header'),
    dcc.Dropdown(id='vehicle-data-name',
                 options=[{'label': s, 'value': s}
                          for s in user_data.keys()],
                 value=["Heavy-Autumn-Wolf", "Quick-Grove-Mind", "Mercury-Wood-Sprite"],
                 multi=True
                 ),
    html.Div(children=html.Div(id='graphs', className='row'), className='container-fluid'),
    html.Div([
        html.H3('Top 25 Notional', className='ranker-header'),
        dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in df_test.columns],
            data=df_test.to_dict('records'),
            style_cell={'textAlign': 'left'},
            style_cell_conditional=[
                {
                    'if': {'column_id': 'Region'},
                    'textAlign': 'left'
                }
            ],
            export_format='xlsx',
            export_headers='display',
            merge_duplicate_headers=True,
            style_data_conditional=[
                {
                    'if': {
                        'column_id': 'PNL',
                        'filter_query': '{PNL} < 0'
                    },
                    'color': 'red',
                },
                {
                    'if': {
                        'column_id': 'PNL',
                        'filter_query': '{PNL} > 0'
                    },
                    'color': 'green',
                },
            ],
            style_header={'backgroundColor': 'rgb(230, 230, 230)','fontWeight': 'bold'}
        )
    ]),
    dcc.Interval(
        id='graph-update',
        interval=500),
    html.Section([
        html.H3('About'),
        html.Span(about_text,
                 className='bitmex-ranker-logo',
                 style={'height': '20vh', 'padding': '2%'}
                 ),
        html.A('by @robwc', className='bitmex-ranker-robswc')
    ], id='about-section'),
    ], className="container", style={'width': '90%', 'max-width': 50000})


@app.callback(dash.dependencies.Output('graphs', 'children'), [dash.dependencies.Input('vehicle-data-name', 'value'), dash.dependencies.Input('my-date-picker-range', 'start_date'), dash.dependencies.Input('my-date-picker-range', 'end_date')])
def update_graph(data_names, start_date, end_date):
    print('UPDATE GRAPHS RAN')
    print('BLANK =====', start_date, end_date)
    fetch_users('notional', generate_list('top 25', 'notional', dt.today().strftime('%Y-%m-%d')), start_date, end_date)
    build_leaderboard_table(user_data)
    graphs = []
    class_choice = 'col-xl-4'

    for data_name in data_names:

        data = go.Scatter(
            x=user_data[data_name]['datestamp'],
            y=user_data[data_name]['profit'],
            name='Scatter',
            marker=dict(
                size=8,
                color=colors[data_names.index(data_name)],  # set color equal to a variable
                )
            )

        time.sleep(0.01)
        graphs.append(html.Div(dcc.Graph(
            id=data_name,
            animate=False,
            figure={'data': [data], 'layout': go.Layout(title='{}'.format(data_name),
                                                        xaxis={'title': 'Date', 'autorange': True},
                                                        yaxis={'title': 'BTC', 'autorange': True})}
            ), className=class_choice))

    return graphs


for css in external_css:
    app.css.append_css({"external_url": css})

external_js = ['https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/js/materialize.min.js']
for js in external_css:
    app.scripts.append_script({'external_url': js})


if __name__ == '__main__':
    app.run_server(debug=True)
