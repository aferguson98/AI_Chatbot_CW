import json
from urllib.request import urlopen

from bs4 import BeautifulSoup as soup


def scrape(journey_data):
    """

    Parameters
    ----------
    journey_data

    Returns
    -------

    """
    if journey_data['returning']:
        url_return = "/{}/{}/dep"
        url_return = url_return.format(
            journey_data['return_date'].strftime("%d%m%Y"),
            journey_data['return_date'].strftime("%H%M")
        )
        inbound_req = "true"
    else:
        url_return = ""
        inbound_req = "false"

    url = ("https://ojp.nationalrail.co.uk/service/timesandfares/{}/{}" 
           "/{}/{}/dep{}")
    url = url.format(journey_data['depart'], journey_data['arrive'],
                     journey_data['departure_date'].strftime("%d%m%y"),
                     journey_data['departure_date'].strftime("%H%M"),
                     url_return)

    # Open the webpage
    webpage = urlopen(url)

    # Transform page into HTML
    html = webpage.read()

    # Breakdown HTML into elements
    page_scrape = soup(html, "html.parser")

    # Get element with "has-cheapest" in the class
    cheap_elements = page_scrape.find("td", {"class": "fare has-cheapest"})

    # Get content of the script tag
    cheap_script = cheap_elements.find('script').contents

    # Strip the text from special chars
    stripped_cheap_text = str(cheap_script).strip("'<>() ").replace(
        '\'', '\"').replace('\00', '').replace('["\\n\\t\\t\\t', "").replace(
        '\\n\\t\\t"]', "")
    print(stripped_cheap_text)

    # Turn json into dictionary
    json_cheap = json.loads(stripped_cheap_text)

    return url, json_cheap
