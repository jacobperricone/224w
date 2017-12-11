import datetime
import glob
import re
import os
import xml.etree.ElementTree as ET
import blocks.savemany_list_of_dicts_to_peewee.core as slodtp
from objects import *
import data_utils as u


DATA_DIR = os.path.join(os.path.dirname(os.getcwd()), 'Data')
PLOT_DIR = os.path.join(os.path.dirname(os.getcwd()), 'Plots')
DATA_PATHS = glob.glob(os.path.join(DATA_DIR, '*.xml'))
DATA_DICT = {os.path.basename(x.strip('.xml')): x for x in DATA_PATHS}



INTEGER_VALS = ['AcceptedAnswerId', 'OwnerUserId', 'Id', 'ViewCount','CommentCount', 'AnswerCount',
                'Score', 'FavoriteCount']




known_tags_path = os.path.join(DATA_DIR, 'known_tags.csv')
known_ids_path = os.path.join(DATA_DIR, 'known_ids2.csv')

with open(known_tags_path, 'r') as f:
    KNOWN_PYTHON_TAGS = set([x.strip() for x in f.readlines()])
with open(known_ids_path, 'r') as f:
    KNOWN_PYTHON_IDS = set([x.strip() for x in f.readlines()])


def boost_it(list_of_dicts):
    for dict in list_of_dicts:
        yield dict



def clean_tags(dict):
    """
    :desc: this function ensuring all column names are present in the row dictionary ad and casts the appropriate
    columns to ints
    :param dict: a dictionary specifying one column in the TAGS tables
    :return: a cleaned version of the dictionary
    """
    TAG_KEYS = Tags._meta.columns.keys()
    for k, v in dict.items():
        if k != 'TagName':
            dict[k] = int(v)
    for key in TAG_KEYS:
        if key not in dict.keys():
            dict[key] = None
    return dict


def create_tag_table(filename=DATA_DICT['Tags']):
    """
    :param filename: path to TAG XML
    :return: NOTHING
    """
    tree = ET.parse(filename)
    root = tree.getroot()
    results = [clean_tags(x.attrib) for x in root]
    slodtp.main(results, db, Tags, boost_it)


def check_post_relevance(dict):
    """
    :desc: check_post_relevance checks a post to determine whether it is a question pertaining to python.
    :param dict: the xml attribute dictionary
    :return: True or False depending on whether the post pertains to a question or not
    """
    tag_strips = [x for x in re.split('< | >', dict.get('Tags', '')) if not x]
    if dict.get('PostTypeId', None) not in ['1']:
        return False
    if dict.get('Id', None) in KNOWN_PYTHON_IDS:
        return True
    if any('python' in s for s in tag_strips):
        return True
    if 'python' in dict.get('Title'):
            return True
    if 'python' in dict.get('Body'):
            return True
    else:
        return False


def parse_questions(filename = DATA_DICT['Posts']):
    """
    :desc: This function takes as input a path the Posts.xml provided by the StackExchange Data Dumpe
    It processes each line of the file extracting only questions known to be associated with python tags, uploading
    to the PostQuestion Database every 10,000 results
    :param filename: path to POST.xml file
    :return: None
    """
    _columns = QuestionPosts._meta.columns
    QUESTION_KEYS = _columns.keys()
    INTEGER_VALS = [k for k,v in _columns.items() if type(v) in [peewee.IntegerField,  peewee.PrimaryKeyField]]
    DATETIME_VALS = [k for k,v in _columns.items() if type(v) in [peewee.DateTimeField]]
    results = []
    iter = 1
    for event, elem in ET.iterparse(filename):
        attrib_dict = elem.attrib
        attrib_keys =  attrib_dict.keys()
        try:
            if check_post_relevance(attrib_dict):
                body = u.parse_body(attrib_dict['Body'])
                result = {}
                for key in QUESTION_KEYS:
                    if key in attrib_keys:
                        if key in INTEGER_VALS:
                            result[key] = int(attrib_dict.get(key, None))
                        elif key in DATETIME_VALS:
                            result[key] = datetime.datetime.strptime(attrib_dict['CreationDate'].split('T')[0], '%Y-%m-%d')
                        else:
                            result[key] = attrib_dict[key]
                    else:
                        result[key] = None
                result['TextBody'] = body['text']
                result['CodeBody'] = body['code']
                results.append(result)
                if len(results) % 10000 == 0:
                    print("Uploading iter {} to db: {} entries uploaded".format(iter, iter*10000))
                    iter +=1
                    slodtp.main(results, db, QuestionPosts, boost_it)
                    results = []
                elem.clear()
            else:
                elem.clear()
                continue

        except Exception as e:
            elem.clear()
            print("Error parsing {}".format(e))
            print(attrib_dict)

    slodtp.main(results, db, QuestionPosts, boost_it)


def parse_post_links(filename = DATA_DICT['PostLinks']):
    """

    :param filename:
    :return:
    """

    _columns = PostLinks._meta.columns
    LINK_KEYS = _columns.keys()
    INTEGER_VALS = [k for k,v in _columns.items() if type(v) in [peewee.IntegerField,  peewee.PrimaryKeyField]]
    DATETIME_VALS = [k for k,v in _columns.items() if type(v) in [peewee.DateTimeField]]
    python_ids = set([z.Id for z in QuestionPosts.select(QuestionPosts.Id)])
    results = []
    iter = 1

    for event, elem in ET.iterparse(filename):
        attrib_dict = elem.attrib
        attrib_keys =  attrib_dict.keys()
        try:
            if int(attrib_dict['PostId']) in python_ids or int(attrib_dict['RelatedPostId']) in python_ids:
                result = {}
                for key in LINK_KEYS:
                    if key in attrib_keys:
                        if key in INTEGER_VALS:
                            result[key] = int(attrib_dict.get(key, None))
                        elif key in DATETIME_VALS:
                            result[key] = datetime.datetime.strptime(attrib_dict['CreationDate'].split('T')[0], '%Y-%m-%d')
                        else:
                            result[key] = attrib_dict[key]
                    else:
                        result[key] = None
                results.append(result)
                if len(results) % 1000 == 0:
                    print("Uploading iter {} to db: {} entries uploaded".format(iter, iter*1000))
                    iter +=1
                    slodtp.main(results, db, PostLinks, boost_it)
                    results = []
                elem.clear()
            else:
                elem.clear()
                continue
        except Exception as e:
            elem.clear()
            print("Error parsing {}".format(e))
            print(attrib_dict)

    slodtp.main(results, db, PostLinks, boost_it)


def create_related_links(linked_query = os.path.join(DATA_DIR, 'related_links.csv'),
                   id_to_qid = os.path.join(DATA_DIR, 'url_question.csv')):
    qid_dict = {}
    with open(id_to_qid, 'r') as f:
        for line in f.readlines()[1:]:
            url, id = line.split(',')
            if url == 'NULL':
                continue
            else:
                qid = int(url.split('/')[4])
                qid_dict[id] = qid
    results = []
    iter = 1

    with open(linked_query, 'r') as f:
        for i,line in enumerate(f.readlines()[1:]):
            try:
                url, qid = line.split(',')
                if url == 'NULL':
                    print("no url in {}".format(line))
                    continue
                RelatedPostId = int(url.split('/')[4])
                PostId = qid_dict[qid]
                result = {'PostId': int(PostId), 'RelatedPostId': RelatedPostId, 'LinkTypeId': 2}
                results.append(result)
                if len(results) % 5000 == 0:
                    print("Uploading iter {} to db: {} entries uploaded".format(iter, iter*5000))
                    iter +=1
                    slodtp.main(results, db, RelatedPostLinks, boost_it)
                    results = []
            except Exception as e:
                print("Error parsing line {}, {}".format(e, line))


def clean_up_questions(filename = DATA_DICT['Posts']):

    _columns = QuestionPosts._meta.columns
    QUESTION_KEYS = _columns.keys()
    INTEGER_VALS = [k for k,v in _columns.items() if type(v) in [peewee.IntegerField,  peewee.PrimaryKeyField]]
    DATETIME_VALS = [k for k,v in _columns.items() if type(v) in [peewee.DateTimeField]]
    results = []
    iter = 1


    # with open(os.path.join(DATA_DIR, 'unfetched_source_posts.csv'), 'r') as f:
    #     additional_ids = set([x.strip() for x in f.readlines()])
    # with open(os.path.join(DATA_DIR, 'unfetched_target_posts.csv'), 'r') as f:
    #     additional_ids = additional_ids | set([x.strip() for x in f.readlines()])
    # print("Processing {} additional ids".format(len(additional_ids)))
    additional_ids = set([z.Id for z in QuestionPosts.select(QuestionPosts.Id, QuestionPosts.TextBody).where(QuestionPosts.TextBody.is_null(True))])

    for event, elem in ET.iterparse(filename):
        attrib_dict = elem.attrib
        attrib_keys =  attrib_dict.keys()
        try:
            if attrib_dict['Id'] in additional_ids:
                body = u.parse_body(attrib_dict['Body'])
                result = {}
                for key in QUESTION_KEYS:
                    if key in attrib_keys:
                        if key in INTEGER_VALS:
                            result[key] = int(attrib_dict.get(key, None))
                        elif key in DATETIME_VALS:
                            result[key] = datetime.datetime.strptime(attrib_dict['CreationDate'].split('T')[0], '%Y-%m-%d')
                        else:
                            result[key] = attrib_dict[key]
                    else:
                        result[key] = None
                    result['TextBody'] = body['text']
                    result['CodeBody'] = body['code']
                results.append(result)
                if len(results) % 1000 == 0:
                    print("Uploading iter {} to db: {} entries uploaded".format(iter, iter*1000))
                    iter +=1
                    slodtp.main(results, db, QuestionPosts, boost_it)
                    results = []
                elem.clear()
            else:
                elem.clear()
                continue
        except Exception as e:
            elem.clear()
            print("Error parsing {}".format(e))
            print(attrib_dict)

    slodtp.main(results, db, PostLinks, boost_it)



def create_user_table(filename = DATA_DICT['Users']):
    _columns = Users._meta.columns
    LINK_KEYS = _columns.keys()
    INTEGER_VALS = [k for k,v in _columns.items() if type(v) in [peewee.IntegerField,  peewee.PrimaryKeyField]]
    DATETIME_VALS = [k for k,v in _columns.items() if type(v) in [peewee.DateTimeField]]
    user_ids = set([z.OwnerUserId for z in QuestionPosts.select(QuestionPosts.OwnerUserId)])
    results = []
    iter = 1


    for event, elem in ET.iterparse(filename):
        attrib_dict = elem.attrib
        attrib_keys =  attrib_dict.keys()
        try:
            if int(attrib_dict['Id']) in user_ids:
                result = {}
                for key in LINK_KEYS:
                    if key in attrib_keys:
                        if key in INTEGER_VALS:
                            result[key] = int(attrib_dict.get(key, None))
                        elif key in DATETIME_VALS:
                            result[key] = datetime.datetime.strptime(attrib_dict['CreationDate'].split('T')[0], '%Y-%m-%d')
                        else:
                            result[key] = attrib_dict[key]
                    else:
                        result[key] = None
                results.append(result)
                if len(results) % 5000 == 0:
                    print("Uploading iter {} to db: {} entries uploaded".format(iter, iter*5000))
                    iter +=1
                    slodtp.main(results, db, Users, boost_it)
                    results = []
                elem.clear()
            else:
                elem.clear()
                continue
        except Exception as e:
            elem.clear()
            print("Error parsing {}".format(e))
            print(attrib_dict)

    slodtp.main(results, db, PostLinks, boost_it)



def parse_answers(filename = DATA_DICT['Posts']):

    _columns = AnswerPosts._meta.columns
    ANSWER_KEYS = _columns.keys()
    INTEGER_VALS = [k for k,v in _columns.items() if type(v) in [peewee.IntegerField,  peewee.PrimaryKeyField]]
    DATETIME_VALS = [k for k,v in _columns.items() if type(v) in [peewee.DateTimeField]]
    results = []
    iter = 1

    parent_ids = set([z.Id for z in QuestionPosts.select(QuestionPosts.Id)])
    retrieved_answers = set([z.Id for z in AnswerPosts.select(AnswerPosts.Id)])

    for event, elem in ET.iterparse(filename):
        attrib_dict = elem.attrib
        attrib_keys =  attrib_dict.keys()
        try:
            if attrib_dict['PostTypeId'] != '2' or int(attrib_dict['Id']) in retrieved_answers:
                elem.clear()
                continue
            else:
                if int(attrib_dict['ParentId']) in parent_ids:
                    result = {}
                    body = u.parse_body(attrib_dict['Body'])
                    for key in ANSWER_KEYS:
                        if key in attrib_keys:
                            if key in INTEGER_VALS:
                                result[key] = int(attrib_dict.get(key, None))
                            elif key in DATETIME_VALS:
                                result[key] = datetime.datetime.strptime(attrib_dict['CreationDate'].split('T')[0], '%Y-%m-%d')
                            else:
                                result[key] = attrib_dict[key]
                        else:
                            result[key] = None
                    result['TextBody'] = body['text']
                    result['CodeBody'] = body['code']
                    results.append(result)
                    if len(results) % 5000 == 0:
                        print("Uploading iter {} to db: {} entries uploaded".format(iter, iter*5000))
                        iter +=1
                        slodtp.main(results, db, AnswerPosts, boost_it)
                        results = []
                    elem.clear()
                else:
                    elem.clear()
                    continue
        except Exception as e:
            elem.clear()
            print("Error parsing {}".format(e))
            print(attrib_dict)

    slodtp.main(results, db, PostLinks, boost_it)













