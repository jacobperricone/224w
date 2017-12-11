from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import os
import gensim
import re
import numpy as np
from sklearn.metrics.pairwise import linear_kernel
from sklearn.metrics.pairwise import cosine_similarity
from objects import *

EMBEDDING_DIR = os.path.join(os.getcwd(), 'Embeddings')
DATA_DIR = os.path.join(os.getcwd(), 'Data')


QT_COMMUNITIES= {}
TT_COMMUNITIES = {}
with open(os.path.join(DATA_DIR, 'QU_T_communities.map'), 'r') as f:
    for line in f.readlines():
        k,v = line.strip().split(',')
        QT_COMMUNITIES[k] = v


title_model = gensim.models.Word2Vec.load(os.path.join(EMBEDDING_DIR, 'titles_embeddings')).wv
text_model = gensim.models.Word2Vec.load(os.path.join(EMBEDDING_DIR, 'text_embeddings')).wv
all_model = gensim.models.Word2Vec.load(os.path.join(EMBEDDING_DIR, 'all_embeddings')).wv


class Evaluator():
    def __init__(self, query_node, suggested_nodes, baseline_nodes):

        self.query_node = str(query_node) if type(query_node) == int else query_node
        self.suggested_nodes = [str(x) if isinstance(x, int) else x for x in suggested_nodes]
        self.baseline_nodes = [str(x) if isinstance(x, int) else x for x in baseline_nodes]
        self.all_nodes = [query_node] + suggested_nodes + baseline_nodes

        self.query = QuestionPosts.select().where(QuestionPosts.Id << self.all_nodes)
        self.all_nodes = [str(x) if isinstance(x, int) else str(x) for x in baseline_nodes]
        self.results = list(self.query.dicts())
        self.attributes = list([x for x in self.results[0].keys() if x != 'Id'])
        self.id_to_node = {}
        self.res = {}
        for result in self.results:
            self.id_to_node[str(result['Id'])] = {k: v for k, v in result.items() if k != 'Id'}

        self.suggested_nodes = [x for x in self.suggested_nodes if x in self.id_to_node.keys()]
        self.baseline_nodes = [x for x in self.baseline_nodes if x in self.id_to_node.keys()]
        self.all_nodes = [query_node] +  self.suggested_nodes +  self.baseline_nodes


        self.title_model = title_model
        self.text_model = text_model
        self.all_model = all_model

        self.categories = ['Tags', 'Title', 'Text', 'All']
        # Comm
        self.cat_keys = ['suggested_scores', 'baseline_scores',
                         'avg_suggested_scores', 'avg_baseline_scores',
                         'std_baseline_scores', 'std_suggested_scores']

        self.avg_keys = ['avg_suggested_scores', 'avg_baseline_scores',
                         'std_baseline_scores', 'std_suggested_scores']

    def evaluate(self):
        self.evaluate_tags()
        self.evaluate_titles()
        self.evaluate_text()
        self.evaluate_all()

    def communtiy_overlap(self):
        mean_suggested_score = 0
        std_suggested_score = 0
        mean_baseline_score = 0
        std_baseline_score = 0



        try:
            self.query_comm = QT_COMMUNITIES[self.query_node]
            self.suggested_comms = set([QT_COMMUNITIES[x] for x in self.suggested_nodes if x in QT_COMMUNITIES.keys()])
            self.baseline_comms = set([QT_COMMUNITIES[x] for x in self.baseline_nodes if x in QT_COMMUNITIES.keys()])

            overlap_suggested_baseline = len(self.suggested_comms & self.baseline_comms) / len(self.suggested_comms | self.baseline_comms)
            overlap_suggested_query = len(self.suggested_comms & self.query_comm) / len(
                self.suggested_comms | self.query_comm)

            overlap_baseline_query = len(self.baseline_comms & self.query_comm) / len(
                self.baseline_comms | self.query_comm)

            print('{:~^60}'.format('Comm Overlap'))
            print('{:^60}'.format('Suggested'))
            print("Overlap Suggested Baseline: {}".format(overlap_suggested_baseline))
            print("Overlap Suggested Query: {}".format(overlap_suggested_query))
            print('{:^60}'.format('Baseline'))
            print("Overlap Baseline query : {}".format(overlap_baseline_query))
            print("Std Baseline Tag : {}".format(std_baseline_score))

            self.res['Comm'] = {'suggested_scores': [],
                                'baseline_scores': [],
                                'avg_suggested_scores': overlap_suggested_query,
                                'avg_baseline_scores': overlap_baseline_query,
                                'std_baseline_scores': overlap_suggested_baseline,
                                'std_suggested_scores': 0}


        except Exception as e:
            print("Error in processing community overlap {} {} {} {}".format(e,self.query_node, self.suggested_nodes, self.baseline_nodes))


    def evaluate_tags(self):
        mean_suggested_score = 0
        std_suggested_score = 0
        mean_baseline_score = 0
        std_baseline_score = 0
        suggested_correct = []
        baseline_correct = []

        try:
            split_tags = lambda x: set(re.split('<|>', x))
            query_tags = split_tags(self.id_to_node[self.query_node]['Tags'])
            suggested_tags = [split_tags(self.id_to_node[x]['Tags']) for x in self.suggested_nodes]
            baseline_tags = [split_tags(self.id_to_node[x]['Tags']) for x in self.baseline_nodes]

            suggested_correct = []
            for question_tags in suggested_tags:
                suggested_correct.append(len(question_tags & query_tags) / len(question_tags | query_tags))

            baseline_correct = []
            for question_tags in baseline_tags:
                baseline_correct.append(len(question_tags & query_tags) / len(question_tags | query_tags))

            mean_suggested_score = np.mean(suggested_correct)
            std_suggested_score = np.std(suggested_correct)
            mean_baseline_score = np.mean(baseline_correct)
            std_baseline_score = np.std(baseline_correct)

            print('{:~^60}'.format('Title'))
            print('{:^60}'.format('Suggested'))
            print("Mean Suggested Tag: {}".format(mean_suggested_score))
            print("Std Suggested Tag : {}".format(std_suggested_score))
            print('{:^60}'.format('Baseline'))
            print("Mean Baseline Tag : {}".format(mean_baseline_score))
            print("Std Baseline Tag : {}".format(std_baseline_score))


        except Exception as e:
            print("Failed to evaluate tag {}".format(e))

        self.res['Tags'] = {'suggested_scores': suggested_correct,
                            'baseline_scores': baseline_correct,
                            'avg_suggested_scores': mean_suggested_score,
                            'avg_baseline_scores': mean_baseline_score,
                            'std_baseline_scores': std_baseline_score,
                            'std_suggested_scores': std_suggested_score}

    def average_word_vector(self, text_set, model):
        document_vecs = np.array(
            [np.mean(model[[x for x in doc.split() if x in model.vocab]], axis=0) for doc in text_set],
            dtype=np.float64)
        return document_vecs

    def get_titles(self, nodeset):
        titles = [self.id_to_node[x]['Title'] for x in nodeset]
        titles = [x for x in titles if x]

        return titles

    def get_body(self, nodeset):
        body = [self.id_to_node[x]['TextBody'] for x in nodeset if self.id_to_node[x]['TextBody'] is not None]
        body = [x for x in body if x]

        return body

    def get_all(self, nodeset):
        body = [self.id_to_node[x]['TextBody'] + ' ' + self.id_to_node[x]['Title'] for x in nodeset if
                self.id_to_node[x]['TextBody'] is not None]
        body = [x for x in body if body]
        return body

    def evaluate_titles(self):
        mean_suggested_score = 0
        std_suggested_score = 0
        mean_baseline_score = 0
        std_baseline_score = 0
        suggested_scores = []
        baseline_scores = []

        try:
            suggested_titles = self.get_titles(self.suggested_nodes)
            baseline_titles = self.get_titles(self.baseline_nodes)
            query_node_title = self.get_titles([self.query_node])

            suggested_node_vecs = self.average_word_vector(suggested_titles, self.title_model)
            baseline_node_vecs = self.average_word_vector(baseline_titles, self.title_model)
            query_node_vec = self.average_word_vector(query_node_title, self.title_model)

            suggested_scores = cosine_similarity(query_node_vec, suggested_node_vecs)
            baseline_scores = cosine_similarity(query_node_vec, baseline_node_vecs)

            mean_suggested_score = np.mean(suggested_scores)
            std_suggested_score = np.std(suggested_scores)
            mean_baseline_score = np.mean(baseline_scores)
            std_baseline_score = np.std(baseline_scores)
            print('{:~^60}'.format('Title'))
            print('{:-^60}'.format('Suggested'))
            print("Mean Suggested Cosine Similarity Title: {}".format(mean_suggested_score))
            print("Std Suggested Cosine Similarity Title : {}".format(std_suggested_score))
            print('{:-^60}'.format('Baseline'))
            print("Mean Baseline Cosine Similarity Title : {}".format(mean_baseline_score))
            print("Std Baseline Cosine Similarity Title : {}".format(std_baseline_score))


        except Exception as e:
            print("Failed to evaluate title {}".format(e))

        self.res['Title'] = {'suggested_scores': suggested_scores,
                             'baseline_scores': baseline_scores,
                             'avg_suggested_scores': mean_suggested_score,
                             'avg_baseline_scores': mean_baseline_score,
                             'std_baseline_scores': std_baseline_score,
                             'std_suggested_scores': std_suggested_score}

    def evaluate_all(self):
        mean_suggested_score = 0
        std_suggested_score = 0
        mean_baseline_score = 0
        std_baseline_score = 0
        suggested_scores = []
        baseline_scores = []

        try:
            suggested_docs = self.get_all(self.suggested_nodes)
            baseline_docs = self.get_all(self.baseline_nodes)
            query_doc = self.get_all([self.query_node])

            suggested_node_vecs = self.average_word_vector(suggested_docs, self.all_model)
            baseline_node_vecs = self.average_word_vector(baseline_docs, self.all_model)
            query_node_vec = self.average_word_vector(query_doc, self.all_model)

            suggested_scores = cosine_similarity(query_node_vec, suggested_node_vecs)
            baseline_scores = cosine_similarity(query_node_vec, baseline_node_vecs)

            mean_suggested_score = np.mean(suggested_scores)
            std_suggested_score = np.std(suggested_scores)
            mean_baseline_score = np.mean(baseline_scores)
            std_baseline_score = np.std(baseline_scores)
            print('{:~^60}'.format('All'))
            print('{:-^60}'.format('Suggested'))
            print("Mean Suggested Cosine Similarity ALL: {}".format(mean_suggested_score))
            print("Std Suggested Cosine Similarity All : {}".format(std_suggested_score))
            print('{:-^60}'.format('Baseline'))
            print("Mean Baseline Cosine Similarity All : {}".format(mean_baseline_score))
            print("Std Baseline Cosine Similarity All : {}".format(std_baseline_score))

        except Exception as e:
            print("Failed to evaluate all {}".format(e))

        self.res['All'] = {'suggested_scores': suggested_scores,
                           'baseline_scores': baseline_scores,
                           'avg_suggested_scores': mean_suggested_score,
                           'avg_baseline_scores': mean_baseline_score,
                           'std_baseline_scores': std_baseline_score,
                           'std_suggested_scores': std_suggested_score}

    def evaluate_text(self):

        mean_suggested_score = 0
        std_suggested_score = 0
        mean_baseline_score = 0
        std_baseline_score = 0
        suggested_scores = []
        baseline_scores = []

        try:
            suggested_docs = self.get_body(self.suggested_nodes)
            baseline_docs = self.get_body(self.baseline_nodes)
            query_doc = self.get_body([self.query_node])

            suggested_node_vecs = self.average_word_vector(suggested_docs, self.text_model)
            baseline_node_vecs = self.average_word_vector(baseline_docs, self.text_model)
            query_node_vec = self.average_word_vector(query_doc, self.text_model)

            suggested_scores = cosine_similarity(query_node_vec, suggested_node_vecs)
            baseline_scores = cosine_similarity(query_node_vec, baseline_node_vecs)

            mean_suggested_score = np.mean(suggested_scores)
            std_suggested_score = np.std(suggested_scores)
            mean_baseline_score = np.mean(baseline_scores)
            std_baseline_score = np.std(baseline_scores)

            print('{:~^60}'.format('Text'))
            print('{:-^60}'.format('Suggested'))
            print("Mean Suggested Cosine Similarity Text: {}".format(mean_suggested_score))
            print("Std Suggested Cosine Similarity Text : {}".format(std_suggested_score))
            print('{:-^60}'.format('Baseline'))
            print("Mean Baseline Cosine Similarity Text : {}".format(mean_baseline_score))
            print("Std Baseline Cosine Similarity Text : {}".format(std_baseline_score))

        except Exception as e:
            print("Failed to evaluate Text {}".format(e))

        self.res['Text'] = {'suggested_scores': suggested_scores,
                            'baseline_scores': baseline_scores,
                            'avg_suggested_scores': mean_suggested_score,
                            'avg_baseline_scores': mean_baseline_score,
                            'std_baseline_scores': std_baseline_score,
                            'std_suggested_scores': std_suggested_score}


# s_avg_tag = np.mean([x.res['Tags']['Avg. Tag Overlap Suggested'] for x in es])
# b_avg_tag = np.mean([x.res['Tags']['Avg. Tag Overlap Baseline'] for x in es])
# s_avg_title = np.mean([x.res['Title']['avg_suggested_scores'] for x in es])
# b_avg_title = np.mean([x.res['Title']['avg_baseline_scores'] for x in es])
# s_avg_text = np.mean([x.res['Text']['avg_suggested_scores'] for x in es])
# b_avg_text = np.mean([x.res['Text']['avg_baseline_scores'] for x in es])
# print("Tag Results S/B: {}/{}".format(s_avg_tag,b_avg_tag))
# print("Title Results S/B: {}/{}".format(s_avg_title,b_avg_title))
# print("Text Results S/B: {}/{}".format(s_avg_text,b_avg_text))
#  qnode = 5742119 suggested_nodes =
