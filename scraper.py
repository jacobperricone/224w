import os
import re
import logging
import random
import json
import traceback
import math
import datetime
import blocks.build_lambda_function.core as blf
import blocks.invoke_lambda_function.core as ilf
import blocks.deploy_lambda_function.core as dlf
import blocks.get_ip_address.core as gia
import blocks.authorize_proxy_mesh.core as apm
import blocks.deauthorize_proxy_mesh.core as dpm
import blocks.create_dict_from_element.core as cdfe
import blocks.savemany_list_of_dicts_to_peewee.core as slodtp
import blocks.multithread_with_error_queue.core as mtweq
import blocks.get_element_by_xpath.core as gex
import pandas as pd
from objects import *
from data_utils import *



# RUN = SearchRun.create(date_pulled=datetime.datetime.now())

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logging.getLogger('requests').setLevel(logging.WARNING)



def boost_it(list_of_dicts):
    for dict in list_of_dicts:
        yield dict


def get_headers_and_proxies():
    req_headers = {}
    if USER_AGENTS:
        req_headers['User-Agent'] = random.choice(USER_AGENTS)
    if PROXIES:
        req_proxies = random.choice(PROXIES)
    else:
        req_proxies = []
    return {'headers': req_headers, 'proxies': req_proxies}



def overflow_processor(input, payload_response):
    results = payload_response['results']
    if results:
       # logger.info('SAVING')
        slodtp.main(results, db, input['db'], boost_it)
    else:
        raise Exception('Results are empty!')

def overflow_parse_processor(input, payload_response):
    results = payload_response['results']
    if results:
        for k, v in results.iteritems():
            slodtp.main(v, db, input['db'][k], boost_it)
    else:
        raise Exception('Results are empty!')

def lambda_worker(input):
    try:
        res = ilf.main(input['event'],input['lambda_func'], 'us-east-1', 'AKIAJAFU4HW3FBOJLLZQ',
                       'X1bgOX3moMtaOoRxM4muGIip7zYCv3tY9XoOQ/zb')
        payload = res['Payload']
        payload_response = payload.read()

        if type(payload_response) is str:
            payload_response = json.loads(payload_response)
        else:
            payload_response = payload_response.read()

        if 'FunctionError' in res.keys():
            logger.error('FAILURE! - {}'.format(str(payload_response['errorMessage'])[:200]))
            input.update({'status': 'Failed'})
            return input
        else:
            input['processor'](input, payload_response)
            input.update({'status': 'Processed'})
            return input
    except Exception as e:
        traceback.print_exc()
        print('Exception: Failed on {} error on input'.format(e))
        input.update({'status': 'Failed'})
        return input



def cleanup_stackoverflow_urls():
    run_id = max([x.run.id for x in SearchResult.select(SearchResult.run).distinct()])

    query = SearchResult.select().where(SearchResult.run == run_id, SearchResult.s3_path.is_null(True))
    rows = list(query.dicts())
    inputs =   [{'event': x,
               'db': SearchResult, 'processor': overflow_processor,
               'lambda_func': 'stackoverflow_cleanup_lambda_function'}
              for x in rows
    ]
    logger.info("Processing combos With run {} of length {}".format(run_id, len(inputs)))
    mtweq.main(inputs, lambda_worker, 100, 10, index="status")


def parse_s3_files():
    query = SearchResult.select(SearchResult.s3_path, SearchResult.id).where(SearchResult.s3_path.is_null(False), SearchResult.id.not_in(Questions.select(Questions.question)))
    rows = list(query.dicts())
    inputs =   [{'event': x,
               'db': {'question': Questions, 'answers': Answers, 'related': ConnectedQuestions}, 'processor': overflow_parse_processor,
               'lambda_func': 'stackoverflow_parse_s3'}
              for x in rows
    ]

    mtweq.main(inputs, lambda_worker, 50, 10, index = "status")


def fetch_stackoverflow_urls():
    IP_ADDRESS = gia.main()
    apm.main(IP_ADDRESS, "solutionloft",
                             "fallSL2016!")

    params = get_headers_and_proxies()

    base_url = "https://stackoverflow.com/questions/tagged/python?sort=votes&pageSize=50"
    settings = {"xpath": "//div[@id='questions-count']//*[contains(@class, 'summarycount')]/text()",
                "func": lambda x: int(re.sub(',', '', x[0].xpath(x[1])[0].split(' ')[-1].split('\n')[0]))}

    num_listings = gex.main(base_url, settings, req_proxies=params['proxies'], headers=params['headers'])
    logger.info("Number of listings is {}".format(num_listings))
    num_pages = int(math.ceil(float(num_listings)/50))


    query =  SearchResult.select(SearchResult.page_num).group_by(SearchResult.page_num).having(peewee.fn.Count(SearchResult.page_num) == 50)
    fetched_pages = [x.page_num for x in query]


    inputs = [{'event': {'url': base_url + '&page=' + str(i) , 'run': 14, 'page': i},
               'db': SearchResult, 'processor': overflow_processor,
               'lambda_func': 'stackoverflow_lambda_function'}
              for i in range(1, num_pages) if i not in fetched_pages
    ]

    logger.info("Processing combos With run {}".format(14))
    mtweq.main(inputs, lambda_worker, 25, 10, index="status")

    dpm.main(IP_ADDRESS, "solutionloft",
                             "fallSL2016!")




def main():
    # fetch_stackoverflow_urls()
    # cleanup_stackoverflow_urls()

    parse_s3_files()






if __name__ == '__main__':
    main()










