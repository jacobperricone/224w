from lxml import html
import blocks.create_dict_from_element.core as cdfe
from multiprocessing.pool import ThreadPool
import logging

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/603.2.4 (KHTML, like Gecko) Version/10.1.1 Safari/603.2.4',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.85 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:34.0) Gecko/20100101 Firefox/34.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0'
]

PROXIES = [
    {'http': 'http://solutionloft:fallSL2016!@us-il.proxymesh.com:31280',
     'https': 'http://solutionloft:fallSL2016!@us-il.proxymesh.com:31280'},
    {'http': 'http://solutionloft:fallSL2016!@us.proxymesh.com:31280',
     'https': 'http://solutionloft:fallSL2016!@us.proxymesh.com:31280'},
    {'http': 'http://solutionloft:fallSL2016!@us-dc.proxymesh.com:31280',
     'https': 'http://solutionloft:fallSL2016!@us-dc.proxymesh.com:31280'},
    {'http': 'http://solutionloft:fallSL2016!@us-ca.proxymesh.com:31280',
     'https': 'http://solutionloft:fallSL2016!@us-ca.proxymesh.com:31280'},
    {'http': 'http://solutionloft:fallSL2016!@us-ny.proxymesh.com:31280',
     'https': 'http://solutionloft:fallSL2016!@us-ny.proxymesh.com:31280'},
    {'http': 'http://solutionloft:fallSL2016!@us-ny.proxymesh.com:31280',
     'https': 'http://solutionloft:fallSL2016!@us-ny.proxymesh.com:31280'},
    {'http': 'http://solutionloft:fallSL2016!@de.proxymesh.com:31280',
     'https': 'http://solutionloft:fallSL2016!@de.proxymesh.com:31280'},
    {'http': 'http://solutionloft:fallSL2016!@nl.proxymesh.com:31280',
     'https': 'http://solutionloft:fallSL2016!@nl.proxymesh.com:31280'},
    {'http': 'http://solutionloft:fallSL2016!@sg.proxymesh.com:31280',
     'https': 'http://solutionloft:fallSL2016!@sg.proxymesh.com:31280'},
    {'http': 'http://solutionloft:fallSL2016!@uk.proxymesh.com:31280',
     'https': 'http://solutionloft:fallSL2016!@uk.proxymesh.com:31280'}
]



logger = logging.getLogger('stackoverflow')
logger.setLevel(logging.DEBUG)


def get_code(x):
    """
    parses code from an html body object
    :param x: HTML object
    :return: Code as a string
    """
    try:
        code = x[0].xpath(x[1])
        if len(code):
            if len(code) == 1:
                return code[0].replace('>>>', '').replace('...', '')
            else:
                return "[break]".join(code).replace('>>>', '').replace('...', '\t')
        else:
            return None
    except Exception as e:
        logger.error("Failed in fetching question code: {}".format(e))
        return None


def get_text(x):
    """
    parses text from an html body object
    :param x: HTML object
    :return: Text of body as a string
    """
    try:
        text = x[0].xpath(x[1])
        if len(text):
            if len(text) == 1:
                return text[0]
            else:
                return "\n".join(text)
        else:
            return None
    except Exception as e:
        logger.error("Failed in fetching text {}".format(e, x))
        return None


def parse(page, settings):
    """
    :param page: an html object corresponding to the body to be examined
    :param settings: a dictionary specifiying attributes
    :return: a list of parsed results
    """
    results = []
    try:
        val_xpath = settings['xpath']
        inputs = [(x, settings['per_item'], settings['aux']) for x in page.xpath(val_xpath)]
        # logger.info(inputs)
        if len(inputs) > 1:
            num_processes = 10
            pool = ThreadPool(num_processes)
            results = pool.map(unpack, inputs)
            pool.close()
            pool.join()
        else:
            if inputs:
                results = [cdfe.main(*inputs[0])]
            else:
                results = []
        return results
    except Exception as error:
        logger.info("Failed to get info for data elements with and error {}"
                    .format(error))
        return results


def unpack(x):
    res = cdfe.main(*x)
    return res


def parse_body(body):
    page = html.fromstring(body)
    question_settings = [
        {"keyName": "code",
         "xpath": "//*[local-name() = 'code']/text()",
         "func": get_code,
         "val": None},
        {"keyName": "text",
         "xpath": "//*[local-name() != 'code']/text()",
         "func": get_text,
         "val": None},
    ]

    question_inputs = {
        'settings': {'xpath': ".",
                     "global_entries": [],
                     'aux': [],
                     'per_item': question_settings
                     }
    }

    results = parse(page, **question_inputs)

    return results[0]
