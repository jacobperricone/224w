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
from ..objects import *
from ..data_utils import *
from ..utils import *
from .. import evaluate as eval


UTQ_graph = nx.Graph()

def SET_UTQ_WEIGHTS():
    """
    :return: Set the weights to the TQ_Graph
    """
    min_weighting = 1 / 5000
    for node in filter(lambda x: UTQ_graph.nodes[x]['bipartite'] == 'Question', UTQ_graph.nodes()):
        sum_ = sum(min(1 / UTQ_graph.degree[neighbor], min_weighting * i) for i, neighbor in enumerate(UTQ_graph[node]))
        for i, neighbor in enumerate(UTQ_graph[node]):
            UTQ_graph[node][neighbor]['p'] = min((1 / UTQ_graph.degree[neighbor]), min_weighting * i) / sum_

    for node in filter(lambda x: UTQ_graph.nodes[x]['bipartite'] == 'User', UTQ_graph.nodes()):
        tag_filter = list(filter(lambda x: UTQ_graph.nodes[x]['bipartite'] == 'Tag', UTQ_graph[node]))
        sum_ = sum(UTQ_graph[node][neighbor]['count'] for neighbor in tag_filter)
        for neighbor in tag_filter:
            UTQ_graph[node][neighbor]['p'] = UTQ_graph[node][neighbor]['count'] / sum_


def CREATE_UTQ_GRAPH():
    """
    :desc: instantiate a global Tag->Question Bipartite graph specifying the weighting
    :return:
    """

    query = QuestionPosts.select(QuestionPosts.Id, QuestionPosts.Tags, QuestionPosts.FavoriteCount,
                                 QuestionPosts.ViewCount, QuestionPosts.AcceptedAnswerId, QuestionPosts.OwnerUserId) \
        .where(QuestionPosts.AcceptedAnswerId.is_null(False),
               QuestionPosts.ViewCount.is_null(False), QuestionPosts.OwnerUserId.is_null(False))
    tag_results = list(query.dicts())


    global UTQ_graph

    for result in tag_results:
        if result['Tags']:
            tags = [x for x in re.split('<|>', result['Tags']) if x]
            qId = str(result['Id'])
            user_id = 'U_' + str(result['OwnerUserId'])
            UTQ_graph.add_node(qId, bipartite='Question',favoritecount=result['FavoriteCount'],
                              user=result['OwnerUserId'])
            UTQ_graph.add_node(user_id, bipartite='User')
            UTQ_graph.add_edge(qId, user_id)
            for t in tags:
                if t not in UTQ_graph.nodes():
                    UTQ_graph.add_node(t, bipartite='Tag')
                UTQ_graph.add_edge(qId, t)
                if t not in UTQ_graph[user_id]:
                    UTQ_graph.add_edge(user_id, t, count=1)
                else:
                    UTQ_graph[user_id][t]['count'] += 1
    SET_UTQ_WEIGHTS()
    return UTQ_graph



def get_tag_user(G, user_node):
    """

    :param G: graph
    :param node: Node
    :return: a tag node and a probability of occurannce
    """

    neighbor_tags = list(filter(lambda x: G.nodes[x]['bipartite'] == 'Tag', G[user_node]))
    xks = list(range(len(neighbor_tags)))
    pks = [G[user_node][x]['p'] for x in neighbor_tags]
    custm = stats.rv_discrete(name='custm', values=(xks, pks))
    vals_to_node = {x: neighbor_tags[x] for x in xks}
    outcome = custm.rvs(1) - 1
    tag_node = vals_to_node[outcome]
    return tag_node, pks[outcome]


def get_random_question_node_user(G, tag_node, initial_prob, initial_node):
    bias = 10e-6
    neighbor_questions = list(filter(lambda x: x != initial_node and G.nodes[x]['bipartite'] == 'Question', G[tag_node]))
    xks = list(range(len(neighbor_questions)))

    raw_weights = np.array([1 / (np.abs(G[tag_node][x]['p'] - initial_prob)+ bias) for x in neighbor_questions])
    sum_weights = raw_weights.sum()
    pks = raw_weights / sum_weights
    custm = stats.rv_discrete(values=(xks, pks))
    vals_to_node = {x: neighbor_questions[x] for x in xks}
    outcome = custm.rvs(1) - 1
    question_node = vals_to_node[outcome]
    return question_node, pks[outcome]


def get_random_tag_node(G, node):
    """

    :param G: graph
    :param node: Node
    :return: a tag node and a probability of occurannce
    """
    neighbor_tags = list(G[node])
    xks = list(range(len(neighbor_tags)))
    pks = [G[node][x]['p'] for x in neighbor_tags]
    custm = stats.rv_discrete(name='custm', values=(xks, pks))
    vals_to_node = {x: neighbor_tags[x] for x in xks}
    outcome = custm.rvs(1) - 1
    tag_node = vals_to_node[outcome]
    return tag_node, pks[outcome]


def get_random_question_node(G, tag_node, initial_prob, initial_node):
    """

    :param G: Graph
    :param tag_node: tag node
    :param initial_prob: initial probability
    :param initial_node: initial node so dont link back to it
    :return: a tag node and a probability of occurence
    """
    bias = 10e-6
    neighbor_questions = list(filter(lambda x: x != initial_node and G.nodes[x]['bipartite'] == 'Question', G[tag_node]))
    #start = time.time()
    if len(neighbor_questions) >= 100000:
        rand_idx = random.randint(0, len(neighbor_questions) - 1)
        node = neighbor_questions[rand_idx]
    else:
        numerator = [1 + G.nodes[x].get('favortiecount', 0) * .9 + G.nodes[x].get('viewcount', 0.0) * .00001 for x in
                     neighbor_questions]
        denominator = [1 / (np.abs(G[tag_node][x]['p'] - initial_prob) + bias) for x in neighbor_questions]
        raw_weights = np.array([x * y for x, y in zip(numerator, denominator)])
        sum_weights = raw_weights.sum()
        pks = raw_weights / sum_weights
        node = np.random.choice(neighbor_questions, 1, p=pks)[0]
    # end = time.time()
    #print("Random Question Generation took {}".format(end - start))
    return node, 0.0


def PPR_UTQ(G, start_node, num_steps, alpha, gamma = .3):
    """

    :param G: Graph
    :param start_node: starting nodes
    :param num_steps: maximum number of steps for algo
    :param alpha: restart parameter
    :return:
    """
    z = {}
    node = start_node
    base_user = list(filter(lambda x: G.nodes[x]['bipartite'] == 'User', G[start_node]))[0]
    for i in range(num_steps):
        if i % 100 == 0:
            print("Iteration {}".format(i))

        # Jump to user
        if random.random() <= gamma:
            tag_node, transition_prob = get_tag_user(G, base_user)
            new_node, prob = get_random_question_node_user(G, tag_node, transition_prob, start_node)
            z[new_node] = z.get(new_node, 0) + 1
            node = new_node
        # jump to tag
        else:
            tag_node, transition_prob = get_random_tag_node(G, node)
            new_node, prob = get_random_question_node(G, tag_node, transition_prob, start_node)
            z[new_node] = z.get(new_node, 0) + 1
            node = new_node

        flip = random.random()
        if flip <= alpha:
            node = start_node
        sorted_z = sorted(z.items(), key=operator.itemgetter(1), reverse=True)
        if len(sorted_z) >= 100 and sorted_z[10][-1] >=30:
            break
    sorted_z = sorted(z.items(), key=operator.itemgetter(1), reverse=True)
    return sorted_z



def evaluate_model(G, num_nodes, start_nodes = []):
    if not start_nodes:
        random_nodes = np.random.choice(list(filter(lambda x: G.nodes[x]['bipartite'] == 0, G.nodes())), num_nodes,
                                        replace=False)
    else:
        random_nodes = start_nodes
    Evaluators = []

    for node in random_nodes:
        print("Processing node {}".format(node))
        try:
            baseline_nodes = [str(x.RelatedPostId) for x in
                              RelatedPostLinks.select().where(RelatedPostLinks.PostId == node)]
            if len(baseline_nodes):
                recommendations = PPR_UTQ(G, node, 10000, .3)
                recommended = [x[0] for x in recommendations[0:10]]
                print("Suggested nodes {}".format(recommended))
                e = eval.Evaluator(node, recommended, baseline_nodes)
                Evaluators.append(e)
                # Evaluators_better.append(e2)
                e.evaluate_tags()
                e.evaluate_text()
                e.evaluate_titles()
        except Exception as e:
            print("We have an error with {}: {}".format(node, e))

    return Evaluators
