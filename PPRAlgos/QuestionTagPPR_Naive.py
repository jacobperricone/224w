import datetime
import os
import sys
import numpy as np
import networkx as nx
import collections
import operator
import random
from scipy import stats
import re
from matplotlib import rc
from multiprocessing import Pool
from objects import *
import evaluate_embed as ev

rc('font', **{'family': 'sans-serif', 'sans-serif': ['Helvetica']})
rc('text', usetex=True)

multigraph = nx.MultiDiGraph()
distinct_graph = nx.DiGraph()
TQ_graph = nx.Graph()
UTQ_graph = nx.Graph()


def SET_TQ_WEIGHTS_NAIVE():
    """
    :return: Set the weights to the TQ_Graph
    """
    for node in filter(lambda x: TQ_graph.nodes[x]['bipartite'] == 0, TQ_graph.nodes()):
        sum_ = len(TQ_graph[node])
        for i, neighbor in enumerate(TQ_graph[node]):
            TQ_graph[node][neighbor]['p'] = 1 / sum_


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
            TQ_graph.add_node(qId, bipartite=0, viewcount=result['ViewCount'], favoritecount=result['FavoriteCount'],
                              user=result['OwnerUserId'])
            for t in tags:
                if t not in TQ_graph.nodes():
                    TQ_graph.add_node(t, bipartite=1)
                TQ_graph.add_edge(qId, t)

    SET_TQ_WEIGHTS_NAIVE()
    return TQ_graph


def modifiedPersonalizedPageRank(G, starting_node_set, max_iter=10000):
    """

    :param G: Graph
    :param starting_node_set: starting node set
    :param max_iter: maximum iterations
    :return: sorted list of questions
    """
    tmp = {x: 1 / len(starting_node_set) for x in starting_node_set}
    personalization = dict(tmp, **{x: 0 for x in G.nodes() if x not in starting_node_set})
    ppr = nx.pagerank(G, personalization=personalization, max_iter=max_iter)
    rec_questions = {k: v for k, v in ppr.items() if TQ_graph.nodes[k]['bipartite'] == 0}
    sorted_x = sorted(rec_questions.items(), key=operator.itemgetter(1), reverse=True)
    return sorted_x


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


def get_random_question_node_naive(G, tag_node, initial_prob, initial_node):
    """

    :param G: Graph
    :param tag_node: tag node
    :param initial_prob: initial probability
    :param initial_node: initial node so dont link back to it
    :return: a tag node and a probability of occurence
    """
    bias = 10e-6
    neighbor_questions = list(G[tag_node])
    xks = list(range(len(neighbor_questions)))
    rand_idx = random.randint(0, len(neighbor_questions) - 1)
    random_node = neighbor_questions[rand_idx]
    return random_node, 1 / len(neighbor_questions)


def PPR_NAIVE(G, start_node, num_steps, alpha):
    """

    :param G: Graph
    :param start_node: starting nodes
    :param num_steps: maximum number of steps for algo
    :param alpha: restart parameter
    :return:
    """
    z = {}
    node = start_node
    for i in range(num_steps):
        if i % 100 == 0:
            pass

        tag_node, transition_prob = get_random_tag_node(G, node)
        new_node, prob = get_random_question_node_naive(G, tag_node, transition_prob, start_node)
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

def unpack(x):
    recommendations = PPR_NAIVE(x[0], x[1], 10000, .3)
    return recommendations



def evaluate_model2(G, num_nodes):

    Evaluators = []
    iter = 0
    relevant_nodes = list(filter(lambda x: G.nodes[x]['bipartite'] == 0 and  len(G[x]) >= 3, G.nodes()))

    while iter < num_nodes:

        random.seed(random.randint(1,100))
        nodes = random.sample(relevant_nodes,10)

        print("Processing node {}".format(nodes))

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

        print("Suggested Nodes: {}".format(recommended))
        print("Baseline Nodes: {}".format(baseline_nodes))
        print("evaluated {} nodes".format(len(Evaluators)))

        print_summaries(Evaluators)
        # Evaluators_better.append(e2)



        iter +=1

    print_summaries(Evaluators)
    return Evaluators


if __name__ == '__main__':
    # G = read_QT_graph(os.path.join(DATA_DIR, 'QTPPR.txt'))
    print("starting {}!")
    G = CREATE_TQ_GRAPH()
    results = evaluate_model2(G, 100)
