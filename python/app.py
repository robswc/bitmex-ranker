import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.exceptions import PreventUpdate
import dash_daq as daq
from datetime import datetime as dt
from datetime import date
from threading import Thread
import pickle
import os.path
from os import path
import time

# Bitmex-Ranker imports
from data_handler import get_all_users
from user_constructor import User, get_ranks_range, UserHandler
from table_constructor import TableConstructor
from data_stories import build_data_stories, parse_story, get_story_titles

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

user_handler = UserHandler()
user_handler.activate_all_users()
print('ACTIVE:', user_handler.activated_users)


def get_markdown(file):
    """
    Get markdown file, read it
    :param file:
    :return: markdown file
    """
    return open(file, 'r').read()


class BlockConstructor:
    """
    Handles the HTML and APP aspects of creating blocks.
    """
    def __init__(self):
        self.blocks = {}
        self.threads = []

    def thread_block(self, user, start, end, graph_method, xbt_subplot):
        """
        Creates a block in a separate thread.
        """
        block = user_handler.activated_users.get(user).build_block(start, end, graph_method, xbt_subplot)
        if user in self.blocks:
            pass
        else:
            self.blocks.update({user: block})

    def build_blocks(self, users, start, end, graph_method, xbt_subplot):
        """
        Takes users, creates separate blocks for each user.
        """
        self.blocks.clear()
        for t in self.threads:
            t.join()
        self.blocks.clear()

        for user in users:
            t = Thread(target=self.thread_block(user, start, end, graph_method, xbt_subplot))
            t.start()
            self.threads.append(t)

    def render_blocks(self):
        """
        Render the blocks, currently in self.blocks.
        Will wait for all threads to finish, to avoid double requests.
        """
        blocks = []

        for t in self.threads:
            t.join()

        for k, v in self.blocks.items():
            blocks.append(v)

        return blocks


# Create class objects.
block_constructor = BlockConstructor()
table_constructor = TableConstructor()

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div([

    html.Header(html.Script(src=app.get_asset_url('gtag.js'))),

    # Announcement Banner
    dcc.Markdown(get_markdown('announcement.md'), className='announcement-bar'),

    # Site Header
    html.Div([
        html.Img(src='https://github.com/Robswc/bitmex-ranker/raw/master/img/bitmex-ranker-logo.png',
                 className='bitmex-ranker-logo'
                 ),
        html.Div([
            dcc.Markdown(get_markdown('sitedescription.md')),
            html.Details([
                html.Summary('Data Stories'),
                html.Div(className='data-story-container'),
                html.Div(build_data_stories(), className='data-story-container'),
            ])
        ]),

    ], className='site-header-container'),

    # Start of Graphs Section.
    html.Div([html.H3('Graphs', className='custom-header')]),
    html.Details([
        html.Summary('Parameters'),
        html.Div([
            dcc.DatePickerRange(
                id='date-picker',
                min_date_allowed=dt(2019, 9, 5).date(),
                max_date_allowed=date.today(),
                initial_visible_month=date.today(),
                start_date=dt(2019, 9, 5).date(),
                end_date=date.today()
            ),
            dcc.RadioItems(
                options=[
                    {'label': 'Notional', 'value': 'notional'},
                    {'label': 'Notional USD', 'value': 'notional_usd'}
                ],
                value='notional',
                id='graph-method',
                labelStyle={'display': 'inline-block'},
                className='radio-container'
            ),
            daq.BooleanSwitch(
                id='xbt-subplot',
                label='XBT Subplot',
                labelPosition='left',
                on=False
            ),

            # dcc.Upload(
            #     id='upload-data',
            #     children=html.Div([
            #         'Plot custom curve, Drag and Drop or ',
            #         html.A('Select Files')
            #     ]),
            #     style={
            #         'width': '100%',
            #         'height': '60px',
            #         'lineHeight': '60px',
            #         'borderWidth': '1px',
            #         'borderStyle': 'dashed',
            #         'borderRadius': '5px',
            #         'textAlign': 'center',
            #         'margin': '10px'
            #     },
            #     # Allow multiple files to be uploaded
            #     multiple=True
            # ),

        ], className='parameters-container'),

        dcc.Dropdown(
            id='graph-dropdown',
            options=[{'label': s, 'value': s} for s in get_all_users()],
            multi=True,
            value=get_ranks_range(0, 3),
        ),

    ], className='custom-details data-stories-container'),


    dcc.Loading(id='block-container', className='blocks-container', type='default'),

    html.Hr(),

    # Start of leaderboard section.
    html.H3('Leaderboard', className='custom-header'),
    html.Details([
        html.Summary('Parameters'),
        html.Div([

            # dcc.DatePickerSingle(
            #     id='date-picker-leaderboard',
            #     min_date_allowed=dt(2019, 9, 4).date(),
            #     max_date_allowed=date.today(),
            #     initial_visible_month=date.today(),
            #     date=date.today()
            # ),

            html.P('More coming soon!')

        ], className='parameters-container'),



    ], className='custom-details'),

    # Leaderboard Table
    html.Div(table_constructor.build_table(user_handler.top_25(), ['', 'Rank', 'Name', 'Profit', 'USD Profit', 'PNL Day'])),

    # Questions and Answers
    html.H3('Questions and Answers'),
    dcc.Markdown(get_markdown('questionsanswers.md')),

    html.P('Disclaimer: Bitmex Ranker is not associated or affiliated with Bitmex.com.'),

], className='main-layout')


# Main callback.
@app.callback(
    dash.dependencies.Output('block-container', 'children'),
    [dash.dependencies.Input('graph-dropdown', 'value'),
     dash.dependencies.Input('date-picker', 'start_date'),
     dash.dependencies.Input('date-picker', 'end_date'),
     dash.dependencies.Input('graph-method', 'value'),
     dash.dependencies.Input('xbt-subplot', 'on')],
    [dash.dependencies.State('block-container', 'children')])
def update_output(value, start_date, end_date, graph_method, xbt_subplot, existing_state):

    if value == get_ranks_range(0, 3):
        if path.exists('cache/default-{}.obj'.format(date.today())):
            filehandler = open('cache/default-{}.obj'.format(date.today()), 'rb')
            blocks = pickle.load(filehandler)
        else:
            block_constructor.build_blocks(value, start_date, end_date, graph_method, xbt_subplot)
            blocks = block_constructor.render_blocks()
            file_recording = open('cache/default-{}.obj'.format(date.today()), 'wb')
            pickle.dump(blocks, file_recording)
    else:
        print('Building Blocks...\n{}'.format(value))
        print(block_constructor.threads)
        block_constructor.build_blocks(value, start_date, end_date, graph_method, xbt_subplot)
        blocks = block_constructor.render_blocks()

    return blocks


# Parameters Callback.
lb_buttons = [dash.dependencies.Input('lb-button-{}'.format(user).replace('.', '-'), 'n_clicks') for user in user_handler.top_25()]
data_story_buttons = [dash.dependencies.Input('story-{}'.format(t).replace('.', '-'), 'n_clicks') for t in get_story_titles()]


@app.callback(
    # Outputs
    [dash.dependencies.Output('graph-dropdown', 'value'),
     dash.dependencies.Output('date-picker', 'start_date'),
     dash.dependencies.Output('date-picker', 'end_date')],

    # Inputs
    lb_buttons + data_story_buttons,

    # States
    [dash.dependencies.State('graph-dropdown', 'value'),    # -3
     dash.dependencies.State('date-picker', 'start_date'),  # -2
     dash.dependencies.State('date-picker', 'end_date')])   # -1
def update(*args):
    context = dash.callback_context.triggered[0]

    # Leaderboard Buttons
    if 'lb_' in context.get('prop_id'):
        if context.get('value') is None:
            return args[-3]
        else:
            user = dash.callback_context.triggered[0].get('prop_id').split('.')[0].replace('lb-button-', '')
            new_values = args[-3]
            new_values.append(user)
        return new_values

    # Data Story Buttons
    if 'story' in context.get('prop_id'):
        if context.get('value') is None:
            raise PreventUpdate
        else:
            title = dash.callback_context.triggered[0].get('prop_id').split('.')[0].replace('story-', '')
            story_info = parse_story(title)
            return story_info.get('users'), dt.strptime(story_info.get('start'), '%m-%d-%Y'), dt.strptime(story_info.get('end'), '%m-%d-%Y')


# Start the app.
if __name__ == '__main__':
    app.run_server(debug=True)