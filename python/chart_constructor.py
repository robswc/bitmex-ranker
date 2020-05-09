import plotly.graph_objects as go
import dash_html_components as html
import dash_core_components as dcc
import json

# Bitmex-Ranker imports
from data_handler import get_user_equity_curve



def build_user_curve_fig(user):
    data = json.loads(get_user_equity_curve(user))
    print(data)
    trace = go.Scatter(
        x=data.get('date'),
        y=data.get('profit'))
    fig = go.Figure(data=trace)

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        showlegend=False,
        margin=dict(l=20, r=20, t=5, b=20),
        xaxis={'title': 'Date', 'rangeslider': {'visible': False}, 'autorange': True},
        yaxis={'title': 'Profit', 'autorange': True},
        dragmode='pan',
    )

    return fig


def build_block(user):
    return html.Div([html.H5(user, className='block-header'), dcc.Graph(figure=build_user_curve_fig(user))])


def build_blocks(users):
    blocks = []
    for user in users:
        blocks.append(build_block(user))
    return html.Div(blocks)