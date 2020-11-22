import bs4
import urllib
import json
import pprint
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as soup

class WebScraper:

    def scrape(self, journeyData):
        # journeyData will store variables extracted from the user input to create the query

        # Norwich - London, 5 Dec 2020, 12:45, return 6 Dec 2020, 13:45
        # Should replace later on with user data from journeyData
        url = "https://ojp.nationalrail.co.uk/service/timesandfares/NRW/LST/051220/1245/dep/061220/1345/dep"

        # Open the webpage
        webpage = urlopen(url)

        # Transform page into HTML
        html = webpage.read()
        
        # Breakdown HTML into elements
        page_scrape = soup(html, "html.parser")

        # Get element with "has-cheapest" in the class
        cheap_elements = page_scrape.find("td", {"class":"fare has-cheapest"})

        # Get content of the script tag
        cheap_script = cheap_elements.find('script').contents

        # Strip the text from special chars
        stipped_cheap_text = str(cheap_script).strip("'<>() ").replace('\'', '\"').replace('\00', '').replace('["\\n\\t\\t\\t', "").replace('\\n\\t\\t"]', "")
        print(stipped_cheap_text)
        
        # Turn json into dictionary        
        json_cheap = json.loads(stipped_cheap_text)

        pprint.pprint(json_cheap)

        # JS makes AJAX request to scrape(), which will return the dictionary info. JS will build the ticket to be displayed into the HTML.

WebScraper.scrape("a", "hello")


# python dict with keys:values of what the bot knows based on user input
# populate these when the user gives them. They start empty
# ask different questions based on what bot knows. I.E. having starting point and time => need destination. etc...
