import requests
from lxml import html
import logging

def main(url, settings,req_proxies = {}, headers = {}, post_data = {}):
    """
    @Block
    :desc: Takes a url, settings dictionary, and optional parameters and fetches the element by applying the function
    in the settings dictionary to the element specified by the xpath value in the settings dictionary. If post_data
    is not none, this block makes a post request.

    :param url: the url from which to fetch the element
    :type start_queue: string
    :example start_queue: 'https://www.cnn.com'

    :param settings: A dictionary with two keys "xpath" and "func".
        settings["xpath"]: xpath of the element on the page that is wanted
        settings["func"]:  takes in a list, with the first element being the html page of the url and the second
        element being the xpath passed in,
    :type settings: dictionary
    :example settings:
            settings = {"xpath": "//div[@class='title'][1]//span[@class='num_products']/text()",
                "func": lambda x: int(re.sub(',', '', x[0].xpath(x[1])[0].split(' ')[-1].split('\n')[0])) }


    :param req_proxies: dictionary of request proxies through which to make the request
    :type req_proxies: dictionary


    :param headers: dictionary of headers for the request
    :type headers: dictionary


    :param post_data: A dictionary if the request is a post request to the api
    :type post_data: dictionary



    :returns: The element requested or None if failure
    :rtype: element
    :example: 10
    """
    try:
        if post_data:
                resp = requests.post(url, headers = headers, proxies = req_proxies)
                page = html.fromstring(resp.text)
                element = settings['func']([page, settings['xpath']])
                return  element
        else:
            resp = requests.get(url, headers = headers, proxies = req_proxies)
            page = html.fromstring(resp.text)
            element = settings['func']([page, settings['xpath']])
            return element
    except Exception, e:
        logging.error("Errror {}".format(e))
        logging.error("Unable to find element with xpath {} on url {} using proxies {} with post_data {}".
                     format(settings['xpath'], url, req_proxies, post_data))
        return None
