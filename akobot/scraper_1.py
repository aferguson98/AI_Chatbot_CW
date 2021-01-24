import json
import re

from bs4 import BeautifulSoup as soup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager


def scrape(journey_data):
    """

    Parameters
    ----------
    journey_data

    Returns
    -------

    """

    if journey_data['returning']:
        url_return = "&inbound=true&inboundTime={}T{}&inboundTimeType=DEPARTURE"
        url_return = url_return.format(
            journey_data['return_date'].strftime("%Y-%m-%d"),
            journey_data['return_date'].strftime("%H:%M:00")
        )
    else:
        url_return = ""

    url = ("https://buy.chilternrailways.co.uk/search?origin=GB{}"
           "&destination=GB{}&outboundTime={}T{}"
           "&outboundTimeType=DEPARTURE&adults={}&children={}{}"
           "&railcards=%5B{}%5D")
    url = url.format(journey_data['depart'], journey_data['arrive'],
                     journey_data['departure_date'].strftime("%Y-%m-%d"),
                     journey_data['departure_date'].strftime("%H:%M:00"),
                     journey_data['no_adults'].strip(),
                     journey_data['no_children'].strip(), url_return, "")

    opts = webdriver.FirefoxOptions()
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument('--headless')
    browser = webdriver.Chrome(GeckoDriverManager().install(), options=opts)
    print(url)
    browser.get(url)
    html = ""

    try:
        WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.ID, 'mixing-deck'))
        )
        html = browser.page_source
    except TimeoutException:
        print("Couldn't load expected element - TIMEOUT")
    finally:
        browser.quit()

    page_scrape = soup(html, "html.parser")
    print(page_scrape)
    cheapest_price_html = page_scrape.find(
        "span", {"class": "basket-summary__total--value"}
    )
    from_station_html = page_scrape.find(
        "span", {"data-elid": "from-station"}
    )
    to_station_html = page_scrape.find(
        "span", {"data-elid": "to-station"}
    )

    cheapest_total_price = re.search('>(.*)<',
                                     str(cheapest_price_html)).group(1)
    from_station = re.search('>(.*)<', str(from_station_html)).group(1)
    to_station = re.search('>(.*)<', str(to_station_html)).group(1)

    return [url, [cheapest_total_price, from_station, to_station]]
