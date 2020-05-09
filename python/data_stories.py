import json
import dash_html_components as html


def format_story_title(title):
    return title.replace(' ', '').replace('?', '')

def get_story_titles():
    titles = []
    with open('data_stories/stories.json') as f:
        data = json.load(f)

    for i in data:
        titles.append(format_story_title(i.get('title')))

    return titles

def get_stories():
    stories = []
    try:
        with open('data_stories/stories.json') as f:
            data = json.load(f)
        for i in data:
            stories.append(i)
    except:
        stories = []

    return stories


def create_story(title, desc, link, start, end, users):
    data = {}
    data.update({'title': title, 'desc': desc, 'link': link, 'start': start, 'end': end, 'users': users})

    json_data = get_stories()
    json_data.append(data)

    with open('data_stories/stories.json', 'w') as f:
        json.dump(json_data, f)


# create_story('The Biggest Whale?',
#              'The largest single account spotted on the Bitmex leaderboards... which quickly turned private.',
#              '',
#              '02-01-2020',
#              '02-29-2020',
#              ['Rainbow-Narrow-Rider'])
#
# create_story('Seven accounts, one owner?',
#              'There could be seven accounts belonging to one owner, based on correlations and patterns!',
#              'https://medium.com/@robswc/bitmexs-mystery-whale-2122b5d3094f',
#              '10-05-2019',
#              '10-12-2019',
#              ['Hot-Relic-Fancier', 'Jade-Platinum-Legs', 'Honeysuckle-South-Rib', 'Cream-White-Ox', 'Linen', 'Big-Rift-Sting', 'Jelly-Mint-Flier'])
#
# create_story('The comeback of a lifetime',
#              'Not sure how it was done, however longtime leaderboard leader Heavy-Autumn-Wolf came back from a huge loss.',
#              '',
#              '01-01-2020',
#              '05-01-2020',
#              ['Heavy-Autumn-Wolf'])
#
# create_story('Impressive equity curve',
#              "One of the best equity curves I've come across!",
#              '',
#              '09-10-2019',
#              '05-01-2020',
#              ['Tree-Surf-Dragon'])

def data_story_constructor(title, desc, link):

    return html.Div([
        html.P([html.B(title)]),
        # html.A('Read More', href=link)
        html.Div([html.P(desc)]),
        html.Button('View', id='story-{}'.format(format_story_title(title)), className='data-story-button')
    ], className='data-story-block')


def build_data_stories():
    stories = []

    for i in get_stories():
        stories.append(data_story_constructor(i.get('title'), i.get('desc'), i.get('link')))

    return stories


def parse_story(title):
    stories = get_stories()
    story_info = {}
    for i in stories:
        if format_story_title(i.get('title')) == title:
            story_info.update({'start': i.get('start'), 'end': i.get('end'), 'users': i.get('users')})

    return story_info

