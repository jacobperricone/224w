import networkx as nx
import os
from objects import *
import pandas as pd
import community
import numpy as np
import matplotlib.pyplot as plt
from community import community_louvain
import operator
import random

GRAPH_DIR = os.path.join(os.getcwd(), 'Data/Graphs')
DATA_DIR = os.path.join(os.getcwd(), 'Data')


def community_layout(g, partition):
    """
    Compute the layout for a modular graph.


    Arguments:
    ----------
    g -- networkx.Graph or networkx.DiGraph instance
        graph to plot

    partition -- dict mapping int node -> int community
        graph partitions


    Returns:
    --------
    pos -- dict mapping int node -> (float x, float y)
        node positions

    """

    pos_communities = _position_communities(g, partition, scale=5.)

    pos_nodes = _position_nodes(g, partition, scale=1.5)

    # combine positions
    pos = dict()
    for node in g.nodes():
        pos[node] = pos_communities[node] + pos_nodes[node]

    return pos

def _position_communities(g, partition, **kwargs):

    # create a weighted graph, in which each node corresponds to a community,
    # and each edge weight to the number of edges between communities
    between_community_edges = _find_between_community_edges(g, partition)

    communities = set(partition.values())
    hypergraph = nx.DiGraph()
    hypergraph.add_nodes_from(communities)
    for (ci, cj), edges in between_community_edges.items():
        hypergraph.add_edge(ci, cj, weight=len(edges))

    # find layout for communities
    pos_communities = nx.spring_layout(hypergraph, **kwargs)

    # set node positions to position of community
    pos = dict()
    for node, community in partition.items():
        pos[node] = pos_communities[community]

    return pos


def _find_between_community_edges(g, partition):

    edges = dict()

    for (ni, nj) in g.edges():
        ci = partition[ni]
        cj = partition[nj]

        if ci != cj:
            try:
                edges[(ci, cj)] += [(ni, nj)]
            except KeyError:
                edges[(ci, cj)] = [(ni, nj)]

    return edges

def _position_nodes(g, partition, **kwargs):
    """
    Positions nodes within communities.
    """

    communities = dict()
    for node, community in partition.items():
        try:
            communities[community] += [node]
        except KeyError:
            communities[community] = [node]

    pos = dict()
    for ci, nodes in communities.items():
        subgraph = g.subgraph(nodes)
        pos_subgraph = nx.spring_layout(subgraph, **kwargs)
        pos.update(pos_subgraph)

    return pos



def Community_Analysis(graph_path, save_path, graphname, draw = False, delimiter = ' ', weighted = False):

    fig_path = graph_path + '.png'

    if weighted:
        g = nx.read_weighted_edgelist(os.path.join(GRAPH_DIR, graph_path), delimiter=delimiter)
    else:
        g = nx.read_edgelist(os.path.join(GRAPH_DIR, graph_path), delimiter=delimiter)

    partition = community_louvain.best_partition(g)

    with open(os.path.join(DATA_DIR, save_path), 'w') as f:
        for k,v in partition.items():
            f.write(str(k) + ',' + str(v) + '\n')

    if draw:
        pos = community_layout(g, partition)
        plt.figure()
        nx.draw(g, pos, node_color=list(partition.values()))
        plt.title('Communties of {}'.format(graphname))
        plt.savefig(os.path.join(GRAPH_DIR, fig_path))
        plt.show()

    return partition


def runner():
    TT_graph = 'UndirectedTagTag.txt'
    QU_T_graph = 'QU_T_Weighted.edgelist'
    QA_T_graph = 'QA_T_Weighted.edgelist'
    U_U_graph = 'U_U_Weighted.edgelist'

    TT_partitions = Community_Analysis(TT_graph, 'TT_communties.map', 'Tag-Tag Graph', delimiter=',')
    QU_T_partitions = Community_Analysis(QU_T_graph, 'QU_T_communities.map', 'User (Question)-Tag Graph', weighted= True)
    QA_T_partitions = Community_Analysis(QA_T_graph, 'QU_A_communities.map', 'User (Answer)-Tag Graph',weighted= True)
    UU_partitions = Community_Analysis(U_U_graph, 'U_U_communities.map', 'User (Answer)-Tag Graph',weighted= True)


def load_partitions(path):
    PARTITION = {}

    with open(os.path.join(DATA_DIR,path), 'r') as f:
        for line in f.readlines():
            k, v = line.strip().split(',')
            PARTITION[k] = int(v)

    return PARTITION

def load_graphs(graph_path, weighted = True, delimiter = ' '):
    if weighted:
        g = nx.read_weighted_edgelist(os.path.join(GRAPH_DIR, graph_path), delimiter=delimiter)
    else:
        g = nx.read_edgelist(os.path.join(GRAPH_DIR, graph_path), delimiter=delimiter)

    return g

def analyze_communties(partition):
    communtities = np.array(list(partition.values()))
    unique_communities = np.unique(list(partition.values()))

    communtiy_percentages = {x: np.where(communtities == x)[0].shape[0]/ communtities.shape[0] for x in unique_communities}

    return  communtiy_percentages


def restrict_graph_sizes(graph,partition, sizes):
    sorted_sizes = sorted(sizes.items(), key=operator.itemgetter(1), reverse=True)
    largest_communities = [x[0] for x in sorted_sizes[:10]]
    nodes = list(filter(lambda x: partition[x] in largest_communities, graph.nodes))
    subgraph = graph.subgraph(nodes)
    return subgraph

def restrict_graph_random(graph,partition, sizes):
    random.seed(random.randint(1,100))
    nodes = random.sample(list(graph.nodes()), 10000)
    subgraph = graph.subgraph(nodes)
    new_partitions = {k:v for k,v in partition.items() if k in nodes}
    return subgraph,new_partitions


def summary(partition,graph):
    sizes = analyze_communties(partition)
    sorted_sizes = sorted(sizes.items(), key=operator.itemgetter(1), reverse=True)
    modularity = community.modularity(partition, graph)
    vals = np.array([x[1] for x in sorted_sizes])
    print(vals)
    cumsum = np.cumsum(vals)
    number_of_communities = len(sizes)
    percentag_of_top_10 = cumsum[10]
    cum_sum_5 = cumsum[:5]
    more_than_one_percent = np.where(vals <= .01)[0][0]
    print("Number of communities {}".format(number_of_communities))
    print("Percent by top 10 {}".format(percentag_of_top_10))
    print("Number of Community with greater than 1 % {}".format(more_than_one_percent))
    print("Modularity {}".format(modularity))

    return {'Num': number_of_communities, '% of 10': percentag_of_top_10,
            ">1%": more_than_one_percent, 'Modularity': modularity, 'cum_sum': cum_sum_5}




def plot_communties():
    TT_com = 'TT_communties.map'
    QU_T_com = 'QU_T_communities.map'
    QA_T_com = 'QU_A_communities.map'
    U_U_com = 'U_U_communities.map'

    TT_graph = 'UndirectedTagTag.txt'
    QU_T_graph = 'QU_T_Weighted.edgelist'
    QA_T_graph = 'QA_T_Weighted.edgelist'
    U_U_graph = 'U_U_Weighted.edgelist'


    path = [TT_com, QU_T_com, QA_T_com, U_U_com]
    graph_paths = [TT_graph, QU_T_graph, QA_T_graph, U_U_graph]
    partitions =list(map(load_partitions, path))

    results= {}
    for i,part in enumerate(partitions):
        if i == 0:
            graph = load_graphs(graph_paths[i], weighted = False, delimiter = ',')
        else:
            graph = load_graphs(graph_paths[i])
        results[path[i].strip('.map')] = summary(part, graph)
        graph.clear()


    # QU_T_graph = load_graphs('QU_T_Weighted.edgelist')
    # QU_T_partition = partitions[1]
    #
    # pos = community_layout(QU_T_graph, QU_T_partition)
    # plt.figure()
    # nx.draw(g, pos, node_color=list(partition.values()))
    # plt.title('Communties of {}'.format(graphname))
    # plt.savefig(os.path.join(GRAPH_DIR, fig_path))
    # plt.show()
    #

