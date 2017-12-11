from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import pandas as pd
import re
import numpy as np
from sklearn.metrics.pairwise import linear_kernel
from objects import *

#
class Evaluator():

    def __init__(self, query_node, suggested_nodes, baseline_nodes):
        self.query_node = query_node
        self.suggested_nodes = suggested_nodes
        self.baseline_nodes = baseline_nodes
        self.all_nodes = [query_node] + suggested_nodes + baseline_nodes
        self.query = QuestionPosts.select().where(QuestionPosts.Id << self.all_nodes )
        self.results = list(self.query.dicts())
        self.attributes = list([x for x in self.results[0].keys() if x != 'Id'])
        self.id_to_node = {}
        self.res = {}
        for result in self.results:
            self.id_to_node[str(result['Id'])] = {k:v for k,v in result.items() if k != 'Id'}

    def evaluate_tags(self):
        split_tags = lambda x: set(re.split('<|>', x))
        query_tags = split_tags(self.id_to_node[self.query_node]['Tags'])
        suggested_tags = [split_tags(self.id_to_node[x]['Tags']) for x in self.suggested_nodes]
        baseline_tags = [split_tags(self.id_to_node[x]['Tags']) for x in self.baseline_nodes]

        suggested_correct = []
        for question_tags in suggested_tags:
            suggested_correct.append(len(question_tags & query_tags)/len(question_tags | query_tags))


        baseline_correct = []
        for question_tags in baseline_tags:
            baseline_correct.append(len(question_tags & query_tags)/len(question_tags | query_tags))

        self.res['Tags'] = {'Avg. Tag Overlap Suggested': np.mean(suggested_correct),
               'Avg. Tag Overlap Baseline': np.mean(baseline_correct),
               'Raw Scores Suggest': suggested_correct,
               'Raw Scores Baseline': baseline_correct}

        print("'Avg. Tag Overlap Suggested: {}".format(np.mean(suggested_correct)))
        print("'Avg. Tag Overlap Baseline: {}".format(np.mean(baseline_correct)))


    def evaluate_titles(self):
        documents = [self.id_to_node[x]['Title'] for x in self.all_nodes]
        tfidf = TfidfVectorizer().fit_transform(documents)
        scores = linear_kernel(tfidf[0:1], tfidf)
        suggested_scores = scores[0,1:1 + len(self.suggested_nodes)]
        baseline_scores = scores[0,1 + len(self.suggested_nodes): 1 + len(self.suggested_nodes) + len(self.baseline_nodes)]


        mean_suggested_score = np.mean(suggested_scores)
        mean_baseline_score = np.mean(baseline_scores)

        print("Mean Suggested Cosine Similarity Title: {}".format(mean_suggested_score))
        print("Mean Baseline Cosine Similarity Title : {}".format(mean_baseline_score))

        self.res['Title'] = {'suggested_scores': suggested_scores, 'baseline_scores': baseline_scores,
                             'avg_suggested_scores': mean_suggested_score, 'avg_baseline_scores': mean_baseline_score}

    def evaluate_text(self):
        documents = ['' if self.id_to_node[x]['TextBody']  is None else self.id_to_node[x]['TextBody'] for x in self.all_nodes]
        tfidf = TfidfVectorizer().fit_transform(documents)
        scores = linear_kernel(tfidf[0:1], tfidf)
        suggested_scores = scores[0,1:1 + len(self.suggested_nodes)]
        baseline_scores = scores[0,
                          1 + len(self.suggested_nodes): 1 + len(self.suggested_nodes) + len(self.baseline_nodes)]

        mean_suggested_score = np.mean(suggested_scores)
        mean_baseline_score = np.mean(baseline_scores)

        print("Mean Suggested Cosine Similarity Text: {}".format(mean_suggested_score))
        print("Mean Baseline Cosine Similarity Text: {}".format(mean_baseline_score))

        self.res['Text'] = {'suggested_scores': suggested_scores, 'baseline_scores': baseline_scores,
                             'avg_suggested_scores': mean_suggested_score, 'avg_baseline_scores': mean_baseline_score}



#
#
# s_avg_tag = np.mean([x.res['Tags']['Avg. Tag Overlap Suggested'] for x in es])
# b_avg_tag = np.mean([x.res['Tags']['Avg. Tag Overlap Baseline'] for x in es])
# s_avg_title = np.mean([x.res['Title']['avg_suggested_scores'] for x in es])
# b_avg_title = np.mean([x.res['Title']['avg_baseline_scores'] for x in es])
# s_avg_text = np.mean([x.res['Text']['avg_suggested_scores'] for x in es])
# b_avg_text = np.mean([x.res['Text']['avg_baseline_scores'] for x in es])
# print("Tag Results S/B: {}/{}".format(s_avg_tag,b_avg_tag))
# print("Title Results S/B: {}/{}".format(s_avg_title,b_avg_title))
# print("Text Results S/B: {}/{}".format(s_avg_text,b_avg_text))
