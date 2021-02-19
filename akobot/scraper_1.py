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
                     journey_data['no_adults'],
                     journey_data['no_children'], url_return, "")

    opts = webdriver.FirefoxOptions()
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--headless")
    browser = webdriver.Firefox(executable_path=GeckoDriverManager().install(),
                                options=opts)
    browser.get(url)
    html = ""

    try:
        WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.ID, 'mixing-deck'))
        )
        element = EC._find_element(browser, (By.CLASS_NAME, 'basket-arrow'))
        element.click()

        html = browser.page_source
    except TimeoutException:
        print("Couldn't load expected element - TIMEOUT")
    finally:
        browser.quit()

    page_scrape = soup(html, "html.parser")
    cheapest_price_html = page_scrape.find(
        "span", {"class": "basket-summary__total--value"}
    )
    from_station_html = page_scrape.find(
        "span", {"data-elid": "from-station"}
    )
    to_station_html = page_scrape.find(
        "span", {"data-elid": "to-station"}
    )

    outbound_leg_html = page_scrape.find(
        "ace-journey-leg", {"data-elid": "basket-outward-leg"}
    )

    print(page_scrape)
    print(page_scrape.find("ace-journey-leg"))
    print(page_scrape.find("ace-journey-leg", {"data-elid": "basket-outward-leg"}))

    outbound_dates_html = outbound_leg_html.find(
        "span", {"data-elid": "basket-journey-date"}
    )

    outbound_duration_html = outbound_leg_html.find(
        "span", {"data-elid": "basket-duration-time"}
    )

    outbound_changes_html = outbound_leg_html.find(
        "span", {"data-elid": "basket-journey-changes"}
    )

    returning_str = ""

    if journey_data['returning']:
        inbound_leg_html = page_scrape.find(
            "ace-journey-leg", {"data-elid": "basket-return-leg"}
        )

        inbound_dates_html = inbound_leg_html.find(
            "span", {"data-elid": "basket-journey-date"}
        )

        inbound_duration_html = inbound_leg_html.find(
            "span", {"data-elid": "basket-duration-time"}
        )

        inbound_changes_html = inbound_leg_html.find(
            "span", {"data-elid": "basket-journey-changes"}
        )

        inbound_datetime = re.search('>(.*)<', str(inbound_dates_html)).group(1)
        inbound_datetime = inbound_datetime.split(",")
        inbound_date = inbound_datetime[0].strip()
        inbound_time = inbound_datetime[1].split("-")[0].strip()
        inbound_duration = re.search('>(.*)<',
                                     str(inbound_duration_html)).group(1)
        inbound_changes = re.search('>(.*)<',
                                    str(inbound_changes_html)).group(1)

        returning_str = (
            " and return {} at {} (duration: {}, {})"
        ).format(inbound_date, inbound_time,  inbound_duration,
                 inbound_changes)

    cheapest_total_price = re.search('>(.*)<',
                                     str(cheapest_price_html)).group(1)
    from_station = re.search('>(.*)<', str(from_station_html)).group(1)
    to_station = re.search('>(.*)<', str(to_station_html)).group(1)
    outbound_datetime = re.search('>(.*)<', str(outbound_dates_html)).group(1)
    outbound_datetime = outbound_datetime.split(",")
    outbound_date = outbound_datetime[0].strip()
    outbound_time = outbound_datetime[1].split("-")[0].strip()
    outbound_duration = re.search('>(.*)<',
                                  str(outbound_duration_html)).group(1)
    outbound_changes = re.search('>(.*)<', str(outbound_changes_html)).group(1)

    info_str = (
        "This service will depart {} at {} (duration: {}, {}){}."
    ).format(outbound_date, outbound_time, outbound_duration, outbound_changes,
             returning_str)

    return [url, [cheapest_total_price.strip(), from_station, to_station,
                  info_str]]
