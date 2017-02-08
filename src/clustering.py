import pandas as pd
import numpy as np
from scipy.sparse import *
from collections import Counter
import logging

from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.externals import joblib
logging.basicConfig(level=logging.INFO)

def load_model():
    return joblib.load('../data/doc_cluster.pkl')

def save_model(model):
    joblib.dump(model,  '../data/doc_cluster.pkl')


def prepare_data(path, corpus = [], total_words = []):
    data = np.load(path)

    for id, event in data.item().items():
        words = [url.rsplit('/', 1)[-1] for url in event]
        total_words.append(words)
        string = ' '.join(words)
        corpus.append(string)

    return corpus, total_words


def vectorize(corpus):
    cv = CountVectorizer()
    vec = cv.fit_transform(corpus)
    terms = cv.get_feature_names()
    return vec, terms


def train_model(vector, num_clusters = 3):

    km = KMeans(n_clusters=num_clusters)

    start = time.time()
    km.fit(vector)
    logging.info(' training took: {}s'.format(time.time() - start))

    clusters = km.labels_.tolist()

    print(Counter(clusters))

    return km

if __name__ == '__main__':
    path = '../data/spotlight_responses.npy'
    corpus, vocab = prepare_data(path)
    vector, terms = vectorize(corpus)
    model = train_model(vector)
