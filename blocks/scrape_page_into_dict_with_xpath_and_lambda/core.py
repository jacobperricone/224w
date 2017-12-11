from random import randint

import requests
from lxml import html

def main(url, settings, headers={}, proxy={}, session=None):
    """
    @Block
    :desc: Take a map of keys and XPaths to extract information from GET
           response from web page.

    :param url: Url of web page to request
    :type url: string
    :example url: "https://news.ycombinator.com/"

    :param settings: List of dictionaries. Each dictionary has three keys. "key"
                     refers to the key that the response for that value will be
                     assigned to in the response. "xpath" refers to the XPATH
                     to pull the matching elements. "func" refers to the lambda function
                     applied to the elements.
    :type settings: list
    :example settings: [{"key": "post_links",
                         "xpath": "//a[@class='storylink'][1]/@href"
                        "func": lambda x: x[0].xpath(x[1])[0] if x[0].xpath(x[1]) else None}]

    :param proxy: A proxy address
    :type proxy: dict
    :example proxy: {"http": "http://solutionloft:fallSL2016!@us-dc.proxymesh.com:31280",
                       "https": "http://solutionloft:fallSL2016!@us-dc.proxymesh.com:31280"}

    :param headers: Dictionary corresponding to request header
    :type headers: dict
    :example headers: {"Referer": product["link"],
                       "Accept": "application/json, text/javascript, */*; q=0.01",
                       "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36"}

    :param session: Optional session if storing cookies is necessary for interacting
                    with the API.
    :type session: requests.sessions.Session

    :returns: A dictionary of values for each dictionary in the settings param.
    :rtype: dict
    :example: {"post_links": ["https://www.bloomberg.com/news/articles/2017-06-16/amazon-to-buy-whole-foods?cmpid=socialflow-twitter-business&utm_content=business&utm_campaign=socialflow-organic&utm_source=twitter&utm_medium=social", "https://techcrunch.com/2017/06/15/justin-kan-atrium-lts-funding/",...]}
    """

    if not session:
        resp = requests.get(url, headers=headers, proxies=proxy)
    else:
        resp = session.get(url, headers=headers, proxies=proxy)

    resp_source = resp.text
    page = html.fromstring(resp_source)
    results = {}

    for setting in settings:
        results[setting['key']] = setting['func']((page, setting['xpath']))

    return results
