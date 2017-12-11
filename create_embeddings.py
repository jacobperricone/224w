
from nltk.corpus import stopwords
import re
import string
import logging
import nltk
from nltk.tokenize import word_tokenize
from objects import *
from gensim.models import Word2Vec

regex = re.compile('[%s]' % re.escape(string.punctuation))




logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

class Text(object):
    def __init__(self, type = 'all'):
        self.query = QuestionPosts.select(QuestionPosts.TextBody, QuestionPosts.Title).where(QuestionPosts.TextBody.is_null(False), QuestionPosts.TextBody.is_null(False))
        self.results = list(self.query.dicts())
        self.text_body = [x['TextBody'].replace('\n', ' ') for x in  self.results]
        self.titles = [x['Title'].replace('\n', ' ') for x in self.results]
        self.all = [x['Title'].replace('\n', ' ') + ' ' + x['TextBody'].replace('\n', ' ')  for x in self.results]
        print(self.all[0:2])
        self.type = type


    def clean(self, line):
        tokenized_sentence = word_tokenize(line)
        clean_sentence = []
        for token in tokenized_sentence:
            if token not in stopwords.words('english'):
                new_token = regex.sub(u'', token)
                if not new_token == u'':
                    clean_sentence.append(new_token)

        return clean_sentence


    def __iter__(self):
        if self.type == 'title':
            for row in self.titles:
                    yield row.split(' ')

        elif self.type == 'body':
            for row in self.text_body:
                    yield row.split(' ')

        else:
            print('all')
            for row in self.all:
                    yield row.split(' ')




if __name__ == '__main__':

    sentences = Text()
    lr = 0.05
    dim = 100
    ws = 8
    epoch = 5
    minCount = 5
    neg = 5
    loss = 'ns'
    t = 1e-4


    params = {
        'alpha': lr,
        'size': dim,
        'window': ws,
        'iter': epoch,
        'min_count': minCount,
        'sample': t,
        'negative': neg,
        'workers': 14
    }

    print("\nCreating Title Embeddings\n")
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    sentences.type = 'title'
    model = Word2Vec(sentences, **params)
    model.save('doc2vec/titles_doc.model')
    #
    print("\nCreating Text Embeddings\n")
    sentences.type = 'body'
    model = Word2Vec(sentences, **params)
    model.save('doc2vec/text_doc.models')

    print("\nCreating Text Embeddings\n")
    sentences.type = 'all'
    model = Word2Vec(sentences, **params)
    model.save('doc2vec/all_doc.model')