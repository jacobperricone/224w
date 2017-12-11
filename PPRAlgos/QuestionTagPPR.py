import datetime
import os
import sys
import numpy as np
import networkx as nx
import operator
import random
from scipy import stats
import re
import time
from matplotlib import rc
from objects import *
import evaluate_embed as ev
from multiprocessing import Pool
import random

rc('font', **{'family': 'sans-serif', 'sans-serif': ['Helvetica']})
rc('text', usetex=True)

TQ_graph = nx.Graph()
DATA_DIR = os.path.join(os.getcwd(), 'Data')
GROUP_DICT = {'tag': 2, 'question': 0}


def SET_TQ_WEIGHTS():
    """
    :return: Set the weights to the TQ_Graph
    """
    min_weighting = 1 / 5000
    for node in filter(lambda x: TQ_graph.nodes[x]['bipartite'] == 0, TQ_graph.nodes()):
        sum_ = sum(min(1 / TQ_graph.degree[neighbor], min_weighting) for i, neighbor in enumerate(TQ_graph[node]))
        for i, neighbor in enumerate(TQ_graph[node]):
            TQ_graph[node][neighbor]['p'] = min((1 / TQ_graph.degree[neighbor]), min_weighting) / sum_


def CREATE_TQ_GRAPH():
    """
    :desc: instantiate a global Tag->Question Bipartite graph specifying the weighting
    :return:
    """

    query = QuestionPosts.select(QuestionPosts.Id, QuestionPosts.Tags, QuestionPosts.FavoriteCount,
                                 QuestionPosts.ViewCount, QuestionPosts.AcceptedAnswerId, QuestionPosts.OwnerUserId) \
        .where(QuestionPosts.AcceptedAnswerId.is_null(False),
               QuestionPosts.ViewCount.is_null(False), QuestionPosts.OwnerUserId.is_null(False))
    tag_results = list(query.dicts())

    global TQ_graph

    for result in tag_results:
        if result['Tags']:
            tags = [x for x in re.split('<|>', result['Tags']) if x]
            qId = str(result['Id'])
            TQ_graph.add_node(qId, bipartite=0, favoritecount=result['FavoriteCount'],
                              user=result['OwnerUserId'])
            for t in tags:
                if t not in TQ_graph.nodes():
                    TQ_graph.add_node(t, bipartite=1)
                TQ_graph.add_edge(qId, t)

    SET_TQ_WEIGHTS()
    return TQ_graph


def read_QT_graph(filename):
    path = os.path.join(DATA_DIR,filename)
    g = nx.read_edgelist(path, delimiter=',')
    return  g




def get_random_tag_node(G, node):
    """

    :param G: graph
    :param node: Node
    :return: a tag node and a probability of occurannce
    """
    neighbor_tags =list(G[node])
    xks = range(len(neighbor_tags))
    pks = [G[node][x]['p'] for x in neighbor_tags]

    tag_idx = np.random.choice(xks, 1, p=pks)[0]
    tag_node = neighbor_tags[tag_idx]

    # custm = stats.rv_discrete(name='custm', values=(xks, pks))
    # vals_to_node = {x: neighbor_tags[x] for x in xks}
    # outcome = custm.rvs(1) - 1
    # tag_node = vals_to_node[outcome]
    return tag_node, pks[tag_idx]


def get_random_question_node(G, tag_node, initial_prob, initial_node):
    """

    :param G: Graph
    :param tag_node: tag node
    :param initial_prob: initial probability
    :param initial_node: initial node so dont link back to it
    :return: a tag node and a probability of occurence
    """
    start = time.time()
    bias = 10e-6
    neighbor_questions = list(G[tag_node])
    xks = list(range(len(neighbor_questions)))
    numerator = [1 + G.nodes[x].get('favortiecount', 0) * .9 for x in
                 neighbor_questions]
    denominator = [1 / (G[tag_node][x]['p'] - initial_prob + bias) for x in neighbor_questions]
    raw_weights = np.array([x * y for x, y in zip(numerator, denominator)])
    sum_weights = raw_weights.sum()
    pks = raw_weights / sum_weights

    custm = stats.rv_discrete(values=(xks, pks))
    vals_to_node = {x: neighbor_questions[x] for x in xks}
    outcome = custm.rvs(1) - 1
    question_node = vals_to_node[outcome]
    end = time.time()
    print("Tag {}, Here Random Question Generation took {}".format(tag_node, end - start))
    return question_node, pks[outcome]


def get_random_question_two(G, tag_node, initial_prob, initial_node):
    """

    :param G: Graph
    :param tag_node: tag node
    :param initial_prob: initial probability
    :param initial_node: initial node so dont link back to it
    :return: a tag node and a probability of occurence
    """

    bias = 10e-6
    neighbor_questions = list(G[tag_node])
    # start = time.time()
    if len(neighbor_questions) >= 10000:
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
    end = time.time()
    # print("Random Question Generation took {}".format(end - start))
    return node, 0.0


def PPR(G, start_node, num_steps, alpha):
    """

    :param G: Graph
    :param start_node: starting nodes
    :param num_steps: maximum number of steps for algo
    :param alpha: restart parameter
    :return:
    """
    z = {}
    node = start_node
    start = time.time()
    for i in range(num_steps):
        if i % 500 == 0:
            end = time.time()
            #print("Iteration {}: took {}".format(i, end - start))
            start = time.time()
        tag_node, transition_prob = get_random_tag_node(G, node)
        new_node, prob = get_random_question_two(G, tag_node, transition_prob, start_node)
        z[new_node] = z.get(new_node, 0) + 1
        node = new_node
        flip = random.random()
        if flip <= alpha:
            node = start_node
        sorted_z = sorted(z.items(), key=operator.itemgetter(1), reverse=True)
        if len(sorted_z) >= 100 and sorted_z[10][-1] >= 20:
            break
    sorted_z = sorted(z.items(), key=operator.itemgetter(1), reverse=True)
    return sorted_z


def print_summaries(Evaluators):
    categories = Evaluators[0].categories
    stats = Evaluators[0].avg_keys

    Avg_Res = {k: {} for k in categories}

    for k in categories:
        for s in stats:
            ress = [x.res[k][s] for x in Evaluators]
            ress = [x for x in ress if x != 0]
            Avg_Res[k][s] = np.mean(ress)
            print("Average of {} / {}: {}".format(k, s, Avg_Res[k][s]))

    return Avg_Res

def evaluate_model(G, num_nodes, start_nodes=[]):
    if not start_nodes:
        random_nodes = np.random.choice(list(filter(lambda x: G.nodes[x]['bipartite'] == 0 and  len(G[x]) >= 3, G.nodes())), num_nodes,
                                        replace=False)
    else:
        random_nodes = start_nodes
    Evaluators = []


    for node in random_nodes:
        print("Processing node {}".format(node))
        try:
            baseline_nodes = [str(x.RelatedPostId) for x in
                              RelatedPostLinks.select().where(RelatedPostLinks.PostId == node)]
            print(baseline_nodes)
            if len(baseline_nodes):
                recommendations = PPR(G, node, 10000, .3)
                recommended = [x[0] for x in recommendations[0:10]]
                e = ev.Evaluator(node, recommended, baseline_nodes)
                e.evaluate()
                Evaluators.append(e)
                print("Suggested nodes {}".format(recommended))
                print("evaluated {} nodes".format(len(Evaluators)))
                # Evaluators_better.append(e2)

        except Exception as e:
            print("We have an error with {}: {}".format(node, e))

    print_summaries(Evaluators)
    return Evaluators


def unpack(x):
    recommendations = PPR(x[0], x[1], 10000, .3)
    return recommendations


def evaluate_model2(G, num_nodes):

    Evaluators = []
    iter = 0
    relevant_nodes = list(filter(lambda x: G.nodes[x]['bipartite'] == 0 and  len(G[x]) >= 3, G.nodes()))

    while iter < num_nodes:

        random.seed(random.randint(1,100))
        nodes = random.sample(relevant_nodes,10)

        print("Processing node {}".format(nodes))
        try:
            baseline_nodes = [[str(x.RelatedPostId) for x in
                              RelatedPostLinks.select().where(RelatedPostLinks.PostId == x)] for x in nodes]
            nodes = [nodes[i] for i in range(len(nodes)) if baseline_nodes[i]]
            baseline_nodes = [x for x in baseline_nodes if baseline_nodes]
            inputs = [(G, x) for x in nodes]
            pool = Pool(6)
            recommendations = pool.map(unpack, inputs)
            pool.close()
            pool.join()

            recommended = [[x[0] for x in y[0:10]] for y in recommendations]

            for i in range(len(nodes)):
                e = ev.Evaluator(nodes[i], recommended[i], baseline_nodes[i])
                e.evaluate()
                Evaluators.append(e)

            print("Suggested nodes {}".format(recommended))
            print("evaluated {} nodes".format(len(Evaluators)))
            print_summaries(Evaluators)
            # Evaluators_better.append(e2)

        except Exception as e:
            print("We have an error with {}: {}".format(nodes, e))

        iter +=1

    print_summaries(Evaluators)
    return Evaluators



def predict(seed_querying):
    print("pr")
    print('Check out ID {}'.format(952914))

if __name__ == '__main__':
    # G = read_QT_graph(os.path.join(DATA_DIR, 'QTPPR.txt'))
    print("starting!")
    G = CREATE_TQ_GRAPH()
    results = evaluate_model2(G, 100)
