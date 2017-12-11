import datetime
import os
import sys
import numpy as np
import networkx as nx
import collections
import pandas as pd
import operator
import random
from scipy import stats
import matplotlib.pyplot as plt
import re
from matplotlib import rc
from objects import *
from data_utils import *
from utils import *
import evaluate as eval

rc('font', **{'family': 'sans-serif', 'sans-serif': ['Helvetica']})
rc('text', usetex=True)
DATA_DIR = os.path.join(os.path.dirname(os.getcwd()), 'Data')


def create_usertag():
    """
    :desc: craet
    :return:
    """

    # Undirected Graph for users with weights as number of interactions
    user_user = nx.Graph()
    user_tag_question = nx.Graph()
    user_tag_answer = nx.Graph()

    query = AnswerPosts.select(AnswerPosts.OwnerUserId, AnswerPosts.ParentId, QuestionPosts.Tags,
                               QuestionPosts.OwnerUserId.alias('QuestionUserId')) \
        .join(QuestionPosts, on=(AnswerPosts.ParentId == QuestionPosts.Id).alias('q'), join_type=peewee.JOIN.LEFT_OUTER)
    results = list(query.dicts())



    for result in results:
        if any(x is None for x in uu_edge):
            continue
        if result['Tags']:
            answerOwnerId = str(result['OwnerUserId'])
            questionOwnerId = str(result['QuestionUserId'])
            tags = [x for x in re.split('<|>', result['Tags']) if x]
            uu_edge = (answerOwnerId, questionOwnerId)

            if user_user.has_edge(*uu_edge):
                user_user[uu_edge[0]][uu_edge[1]]['weight'] += 1
            else:
                user_user.add_edge(*uu_edge, weight = 1)

            utq_edges = [(t, questionOwnerId) for t in tags]
            uta_edges = [(t, answerOwnerId) for t in tags]

            for u,v in utq_edges:
                if user_tag_question.has_edge(u,v):
                    user_tag_question[u][v]['weight'] +=1
                else:
                    user_tag_question.add_edge(u,v, weight = 1)

            for u,v in uta_edges:
                if user_tag_answer.has_edge(u,v):
                    user_tag_answer[u][v]['weight'] +=1
                else:
                    user_tag_answer.add_edge(u,v, weight = 1)



    nx.write_weighted_edgelist(user_user, 'Data/U_U_Weighted.edgelist')
    nx.write_weighted_edgelist(user_tag_answer, 'Data/QA_T_Weighted.edgelist')
    nx.write_weighted_edgelist(user_tag_question, 'Data/QU_T_Weighted.edgelist')



def create_usertag_answer():
    """
    :desc: craet
    :return:
    """
    global usertag_answer, useruser
    query = AnswerPosts.select(AnswerPosts.OwnerUserId, AnswerPosts.ParentId, QuestionPosts.Tags,
                               QuestionPosts.OwnerUserId.alias('QuestionUserId')) \
        .join(QuestionPosts, on=(AnswerPosts.ParentId == QuestionPosts.Id).alias('q'), join_type=peewee.JOIN.LEFT_OUTER)
    tag_results = list(query.dicts())

    for result in tag_results:
        if result['Tags']:
            tags = [x for x in re.split('<|>', result['Tags']) if x]
            answerOwnerId = str(result['OwnerUserId'])
            questionOwnerId = str(result['QuestionUserId'])

            if answerOwnerId not in usertag_answer.nodes():
                usertag_answer.add_node(answerOwnerId, bipartite='User')
            if answerOwnerId not in useruser.nodes():
                useruser.add_node(answerOwnerId)

            if questionOwnerId not in usertag_answer.nodes():
                useruser.add_node(questionOwnerId)

            useruser.add_edge(answerOwnerId, questionOwnerId)

            for tag in tags:
                if tag not in usertag_answer.nodes():
                    usertag_answer.add_node(tag, bipartite='Tags')

                if tag not in usertag_answer[answerOwnerId]:
                    usertag_answer.add_edge(answerOwnerId, tag, count=1)
                else:
                    usertag_answer[answerOwnerId][tag]['count'] += 1
    return usertag_answer


def create_tag_tag_graph(tag_graph):


    query = QuestionPosts.select(QuestionPosts.Tags) \
        .where(QuestionPosts.AcceptedAnswerId.is_null(False),
               QuestionPosts.ViewCount.is_null(False), QuestionPosts.OwnerUserId.is_null(False))
    tag_results = list(query.dicts())
    tag_to_int = {}
    running_max = 0
    for result in tag_results:
        tags = [x for x in re.split('<|>', result['Tags']) if x]
        for t in tags:
            if t not in tag_to_int.keys():
                tag_to_int[t] = running_max
                running_max += 1

    with open(os.path.join(DATA_DIR, tag_graph), 'w') as f:
        for result in tag_results:
            tags = [x for x in re.split('<|>', result['Tags']) if x]
            for i in range(len(tags) - 1):
                f.write(str(tag_to_int[tags[i]]) + ',' + str(tag_to_int[tags[i + 1]]) + '\n')

    with open(os.path.join(DATA_DIR, 'Tag_To_Node'), 'w') as f:
        for k, v in tag_to_int.items():
            f.write(k + ',' + str(v) + "\n")

    return usertag_answer


def create_tag_tag_graph_weighted():
    t_t = nx.Graph()

    query = QuestionPosts.select(QuestionPosts.Tags) \
        .where(QuestionPosts.AcceptedAnswerId.is_null(False),
               QuestionPosts.ViewCount.is_null(False), QuestionPosts.OwnerUserId.is_null(False))
    tag_results = list(query.dicts())
    tag_to_int = {}
    running_max = 0
    for result in tag_results:
        tags = [x for x in re.split('<|>', result['Tags']) if x]
        for t in tags:
            if t not in tag_to_int.keys():
                tag_to_int[t] = running_max
                running_max += 1


    for result in tag_results:
        tags = [x for x in re.split('<|>', result['Tags']) if x]
        for i in range(len(tags) - 1):
            tt_edge = (tag_to_int[tags[i]], tag_to_int[tags[i +1]])
            u,v = tt_edge
            if t_t.has_edge(u,v):
                t_t[u][v]['weight'] += 1
            else:
                t_t.add_edge(u, v, weight=1)

    nx.write_weighted_edgelist(t_t, 'Data/T_T_Weighted.edgelist')

    with open(os.path.join(DATA_DIR, 'Tag_To_Node_Weighted'), 'w') as f:
        for k, v in tag_to_int.items():
            f.write(k + ',' + str(v) + "\n")



def QQ_TT_MULTIEDGE():
    """
    :desc: craet
    :return:
    """
    global multigraph
    query = QuestionPosts.select(QuestionPosts.Id, QuestionPosts.Tags,
                                 QuestionPosts.FavoriteCount, QuestionPosts.ViewCount,
                                 QuestionPosts.AcceptedAnswerId, QuestionPosts.OwnerUserId) \
        .where(QuestionPosts.AcceptedAnswerId.is_null(False),
               QuestionPosts.ViewCount.is_null(False), QuestionPosts.OwnerUserId.is_null(False))
    tag_results = list(query.dicts())

    for result in tag_results:
        if result['Tags']:
            tags = [x for x in re.split('<|>', result['Tags']) if x]
            for i in range(len(tags) - 1):
                if (tags[i], tags[i + 1]) in multigraph.edges():
                    multigraph[tags[i]][tags[i + 1]][0]['count'] += 1
                else:
                    multigraph.add_edge(tags[i], tags[i + 1], count=1)



    return multigraph
