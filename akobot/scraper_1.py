import asyncio
import json
import time

import pyppeteer
from requests_html import HTMLSession, AsyncHTMLSession
from bs4 import BeautifulSoup as soup


async def get_webpage(url):
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    session = AsyncHTMLSession()
    browser = await pyppeteer.launch({
        'ignoreHTTPSErrors': True,
        'headless': True,
        'handleSIGINT': False,
        'handleSIGTERM': False,
        'handleSIGHUP': False
    })
    session._browser = browser
    resp_page = await session.get(url)
    await resp_page.html.arender(keep_page=True)
    return resp_page


def scrape(journey_data):
    """

    Parameters
    ----------
    journey_data

    Returns
    -------

    """

    if journey_data['returning']:
        url_return = "&inboundTime={}T{}&inboundTimeType=DEPARTURE"
        url_return = url_return.format(
            journey_data['return_date'].strftime("%Y-%m-%d"),
            journey_data['return_date'].strftime("%H:%M:00")
        )
        inbound_req = "true"
    else:
        url_return = ""
        inbound_req = "false"

    url = ("https://buy.chilternrailways.co.uk/search?origin=GB{}"
           "&destination=GB{}&adults={}&children={}&outboundTime={}T{}"
           "&outboundTimeType=DEPARTURE&inbound={}{}"
           "&railcards=%5B{}%5D&ls=LS_1_0&ls=LS_2_9&p=PRICE_P_1_8"
           "&p=PRICE_P_2_150")
    url = url.format(journey_data['depart'], journey_data['arrive'],
                     journey_data['no_adults'].strip(),
                     journey_data['no_children'].strip(),
                     journey_data['departure_date'].strftime("%Y-%m-%d"),
                     journey_data['departure_date'].strftime("%H:%M:00"),
                     inbound_req, url_return, "")

    webpage = asyncio.run(get_webpage(url))
    print(webpage.page)
    html = webpage.text
    page_scrape = soup(html, "html.parser")
    print(page_scrape)
    cheap_elements = page_scrape.find(
        "div", {"class": "price-table__cell-content--selectedOut"}
    )
    print(cheap_elements)
    cheap_script = cheap_elements.find('script').contents
    stripped_cheap_text = str(cheap_script).strip("'<>() ").replace(
        '\'', '\"').replace('\00', '').replace('["\\n\\t\\t\\t', "").replace(
        '\\n\\t\\t"]', "")

    # Turn json into dictionary        
    return [url, json.loads(stripped_cheap_text)]
