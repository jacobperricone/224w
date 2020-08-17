from random import randint

import requests
from lxml import html

def main(url, settings, proxies=[], user_agents=[], headers={},
         session=None):
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
                     to arrive at that element. "default" refers to the optional
                     default value that is assigned to the "key" if no elements
                     at the XPath are found.
    :type settings: list
    :example settings: [{"key": "post_links",
                         "xpath": "//a[@class='storylink'][1]/@href"
                        "default": "N/A"}]

    :param proxies: List of proxy addresses
    :type proxies: list
    :example proxies: [{"http": "http://XYZ:fallSL2016!@us-dc.proxymesh.com:31280",
                        "https": "http://XYZ:fallSL2016!@us-dc.proxymesh.com:31280"}]

    :param user_agents: List of user agents
    :type user_agents: list
    :example user_agents: ["Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36"]

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

    req_headers = headers

    if user_agents:
        req_headers["User-Agent"] = user_agents[randint(0,len(user_agents)-1)]

    if proxies:
        req_proxies = proxies[randint(0, len(proxies)-1)]
    else:
        req_proxies = []


    if not session:
        resp = requests.get(url, headers=req_headers, proxies=req_proxies)
    else:
        resp = session.get(url, headers=req_headers, proxies=req_proxies)

    resp_source = resp.text
    page = html.fromstring(resp_source)
    results = {}

    for path in settings:
        val_key = path["key"]
        val_xpath = path["xpath"]
        val_default = path["default"] if "default" in path else None

        if val_default:
            results[val_key] = page.xpath(val_xpath) if page.xpath(val_xpath) else val_default
        else:
            results[val_key] = page.xpath(val_xpath)

    return results
