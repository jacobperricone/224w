import argparse
import logging
import time
import os
import gensim
from gensim.models import Word2Vec
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import pandas as pd
import matplotlib.pyplot as plt

EMBEDDING_DIR = os.path.join(os.getcwd(), 'Embeddings')
DATA_DIR = os.path.join(os.getcwd(), 'Data')


TAGS = []

with open('Data/Tag_To_Node', 'r') as f:
    for line in f.readlines():
        k, _ = line.split(',')
        TAGS.append(k)


logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.WARNING)


def cluster(model_name, k = 10):
    start = time.time()
    print("Load word2vec model ... ", end="", flush=True)
    w2v_model = gensim.models.Word2Vec.load(os.path.join(EMBEDDING_DIR, model_name)).wv
    print("finished in {:.2f} sec.".format(time.time() - start), flush=True)
    word_vectors = w2v_model.syn0

    n_words = word_vectors.shape[0]
    vec_size = word_vectors.shape[1]
    print("#words = {0}, vector size = {1}".format(n_words, vec_size))

    start = time.time()
    print("Compute clustering ... ", end="", flush=True)
    kmeans = KMeans(n_clusters=3, n_jobs=-1, random_state=0)
    idx = kmeans.fit_predict(word_vectors)
    print("finished in {:.2f} sec.".format(time.time() - start), flush=True)

    start = time.time()
    print("Generate output file ... ", end="", flush=True)
    word_centroid_list = list(zip(w2v_model.index2word, idx))
    word_centroid_list_sort = sorted(word_centroid_list, key=lambda el: el[1], reverse=False)
    tag_centroids = [x for x in word_centroid_list_sort if x[0] in TAGS]
    tag_list = [x[0] for x in tag_centroids]
    centroid_list = [x[1] for x in tag_centroids]
    X = w2v_model[tag_list]
    pca = PCA(n_components=2)
    result = pca.fit_transform(X)

    df = pd.concat([pd.DataFrame(result),
                    pd.Series(centroid_list), pd.Series(tag_list)],
                   axis=1)
    df.columns = ['x', 'y', 'cluster', 'word']
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    ax.scatter(df['x'], df['y'], alpha = .2, c = centroid_list)

    random_tag = random.sample(tag_list, 10) + ['python', 'fullscreen', 'pandas', 'uwsgi', 'django', 'subquery', 'java', 'multiprocessing', 'pip']
    for i, row in df[df['word'].isin(random_tag)].iterrows():
        ax.annotate(row['word'], (row['x'], row['y']))

    file_out = open(args.output, "w")
    file_out.write("WORD\tCLUSTER_ID\n")
    for word_centroid in word_centroid_list_sort:
        line = word_centroid[0] + '\t' + str(word_centroid[1]) + '\n'
        file_out.write(line)
    file_out.close()
    print("finished in {:.2f} sec.".format(time.time() - start), flush=True)

    return

if __name__ == "__main__":
    main()