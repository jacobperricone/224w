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

PLOT_DIR = os.path.join(os.path.dirname(os.getcwd()), 'Plots')
# multigraph = nx.MultiDiGraph()
# usertag_answer = nx.Graph()
# usertag_question = nx.Graph()
# useruser = nx.MultiDiGraph()

def plot_alldegree_dist(G, filename):
    indegree_sequence = sorted([d for n, d in G.in_degree()], reverse=True)
    outdegree_sequence = sorted([d for n, d in G.out_degree()], reverse=True)

    outdegreeCount = collections.Counter(outdegree_sequence)
    indegreeCount = collections.Counter(indegree_sequence)
    plt.figure()
    deg, cnt = zip(*outdegreeCount.items())
    plt.loglog(deg, [x / sum(cnt) for x in cnt], label='OutDegree')
    deg, cnt = zip(*indegreeCount.items())
    plt.loglog(deg, [x / sum(cnt) for x in cnt], label='InDegree')
    plt.xlabel("$\log[d]$")
    plt.ylabel("$\log[P(d = k)]$")
    plt.title("Log-Log Plot of Degree-Distribution ")
    plt.legend()
    plt.savefig(os.path.join(PLOT_DIR, filename))


def plot_degree_dist(G, filename):
    test = [(n,d) for n, d in G.degree() if G.nodes[n]]
    degree_sequence = sorted([d for n, d in test if G.nodes[n]['bipartite'] == 'Tags'], reverse=True)
    degreeCount = collections.Counter(degree_sequence)
    plt.figure()
    deg, cnt = zip(*degreeCount.items())
    plt.loglog(deg, [x / sum(cnt) for x in cnt], label='Degree')
    plt.xlabel("$\log[d]$")
    plt.ylabel("$\log[P(d = k)]$")
    plt.title("Log-Log Plot of Degree-Distribution ")
    plt.legend()
    plt.savefig(os.path.join(PLOT_DIR, filename))


def plot_usertag_dist(G, filename):
    test = [(n,d) for n, d in G.degree() if G.nodes[n]]
    degree_sequence_tags = sorted([d for n, d in test if G.nodes[n]['bipartite'] == 'Tags'], reverse=True)
    degree_sequence_users = sorted([d for n, d in test if G.nodes[n]['bipartite'] == 'User'], reverse=True)
    degreeCount_tags = collections.Counter(degree_sequence_tags)
    degreeCount_users = collections.Counter(degree_sequence_users)
    plt.figure()
    deg, cnt = zip(*degreeCount_tags.items())
    plt.loglog(deg, [x / sum(cnt) for x in cnt], label='Tags')
    deg, cnt = zip(*degreeCount_users.items())
    plt.loglog(deg, [x / sum(cnt) for x in cnt], label='Users')
    plt.xlabel("$\log[d]$")
    plt.ylabel("$\log[P(d = k)]$")
    plt.title("Log-Log Plot of Degree-Distribution ")
    plt.legend()
    plt.savefig(os.path.join(PLOT_DIR, filename))


def create_usertag_answer():
    """
    :desc: craet
    :return:
    """
    global usertag_answer, useruser
    query = AnswerPosts.select(AnswerPosts.OwnerUserId, AnswerPosts.ParentId,QuestionPosts.Tags, QuestionPosts.OwnerUserId.alias('QuestionUserId'))\
            .join(QuestionPosts, on = (AnswerPosts.ParentId == QuestionPosts.Id).alias('q'), join_type = peewee.JOIN.LEFT_OUTER)
    tag_results = list(query.dicts())

    for result in tag_results:
        if result['Tags']:
            tags = [x for x in re.split('<|>', result['Tags']) if x]
            answerOwnerId = str(result['OwnerUserId'])
            questionOwnerId = str(result['QuestionUserId'])

            if answerOwnerId not in usertag_answer.nodes():
                usertag_answer.add_node(answerOwnerId, bipartite = 'User')
            if answerOwnerId not in useruser.nodes():
                useruser.add_node(answerOwnerId)

            if questionOwnerId not in usertag_answer.nodes():
                useruser.add_node(questionOwnerId)

            useruser.add_edge(answerOwnerId, questionOwnerId)

            for tag in tags:
                if tag not in usertag_answer.nodes():
                    usertag_answer.add_node(tag, bipartite = 'Tags')

                if tag not in usertag_answer[answerOwnerId]:
                    usertag_answer.add_edge(answerOwnerId, tag, count=1)
                else:
                    usertag_answer[answerOwnerId][tag]['count'] += 1
    return usertag_answer


def QQ_TT_MULTIEDGE():
    """
    :desc: craet
    :return:
    """
    global usertag_answer
    query = QuestionPosts.select(QuestionPosts.Id, QuestionPosts.Tags,
                                 QuestionPosts.FavoriteCount,QuestionPosts.ViewCount,
                                 QuestionPosts.AcceptedAnswerId, QuestionPosts.OwnerUserId) \
        .where(QuestionPosts.AcceptedAnswerId.is_null(False),
               QuestionPosts.ViewCount.is_null(False), QuestionPosts.OwnerUserId.is_null(False))
    tag_results = list(query.dicts())


    return usertag_answer



def QQ_TT_MULTIEDGE():
    """
    :desc: craet
    :return:
    """
    global usertag_answer
    query = QuestionPosts.select(QuestionPosts.Id, QuestionPosts.Tags,
                                 QuestionPosts.FavoriteCount,QuestionPosts.ViewCount,
                                 QuestionPosts.AcceptedAnswerId, QuestionPosts.OwnerUserId) \
        .where(QuestionPosts.AcceptedAnswerId.is_null(False),
               QuestionPosts.ViewCount.is_null(False), QuestionPosts.OwnerUserId.is_null(False))
    tag_results = list(query.dicts())


    return usertag_answer




def QQ_TT_MULTIEDGE():
    """
    :desc: craet
    :return:
    """
    global multigraph
    query = QuestionPosts.select(QuestionPosts.Id, QuestionPosts.Tags,
                                 QuestionPosts.FavoriteCount,QuestionPosts.ViewCount,
                                 QuestionPosts.AcceptedAnswerId, QuestionPosts.OwnerUserId) \
        .where(QuestionPosts.AcceptedAnswerId.is_null(False),
               QuestionPosts.ViewCount.is_null(False), QuestionPosts.OwnerUserId.is_null(False))
    tag_results = list(query.dicts())

    for result in tag_results:
        if result['Tags']:
            tags = [x for x in re.split('<|>', result['Tags']) if x]
            qId = result['Id']
            for i in range(len(tags) - 1):
                if (tags[i], tags[i + 1]) in multigraph.edges():
                    multigraph[tags[i]][tags[i + 1]][0]['count'] += 1
                else:
                    multigraph.add_edge(tags[i], tags[i + 1], count=1)

    return multigraph


def make_plots():
    plot_alldegree_dist(multigraph, 'inout.png')
    plot_degree_dist(multigraph, 'all.png')
