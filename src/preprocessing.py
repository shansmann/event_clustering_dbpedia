"""
script to load and preprocess data
@TODO: REMOVE DUPLICATES
@TODO: BETTER FILTERING OF NOUNS
"""

import config
import time
import glob
import sys
import json
import os
import re
import logging
from sklearn.externals import joblib
from uuid import uuid4

sys.path.append('../external/')
from ClassifierBasedGermanTagger import ClassifierBasedGermanTagger

import numpy as np
import pandas as pd

from yandex_translate import YandexTranslate
translate = YandexTranslate(config.YANDEX_KEY)

logging.basicConfig(level=logging.WARNING)

def load_data():
    """
    loads all files in data/ folder
    """

    data_files = glob.glob(os.path.join('../data/', '*.json'))
    data = []

    for entry in data_files:
        with open(entry) as data_file:
            data.append(json.load(data_file))

    return data[0]


def clean_string(string, regex=r'[^a-zA-Z\s0-9ÄÖÜäöü?ß]+'):
    """
    clean string by removing non chars
    """
    return re.sub(regex, '', string)


def tokenize(string):
    """
    tokenize sentences
    """
    return string.split()


def filter_tags(tags, pos=['NN', 'NE', 'FM']):
    """
    filter tags from model to show nouns
    """
    res = []
    for tag in tags:
        if tag[1] in pos:
            res.append(tag[0])
    return res


def remove_dup(seq):
    """
    remove duplicates from tag list
    """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def load_german_tagger():
    """
    method to load german tagger model
    """
    return joblib.load('german_tagger.sav')


def preprocess_data(key, event, model):
    """
    method preprocesses single event
    @TODO: Use more than descriptions
    """
    if "description" in event:
        description = event['description']
    else:
        description = ''

    if "name" in event:
        name = event['name']
    else:
        name = ''

    event_lookup.append([key, name])
    text = name + ' ' + description

    tokens = tokenize(clean_string(text))
    tags = model.tag(tokens)
    clean_nouns = remove_dup(filter_tags(tags))

    return clean_nouns


def get_translation(word_list):

    n_failed = 0
    tmp = []

    for word in word_list:
        translation = translate.translate(word, 'de-en')
        if translation:
            if translation['code'] != 200:
                n_failed += 1
            else:
                tmp.append(translation['text'][0])
        #time.sleep(0.1)

    logging.warning(' {} / {} req failed'.format(n_failed, len(word_list)))
    return tmp


def get_preprocessed_events(event_data, model):
    data = {}
    n_events = 0
    for day, zones in event_data.items():
        for zone, events in zones.items():
            for i, event in enumerate(events):
                identifier = uuid4()
                preprocessed_event = preprocess_data(identifier, event, model)

                if len(preprocessed_event) == 0:
                    continue

                n_events += 1

                if config.TRANSLATION:
                    preprocessed_event = get_translation(preprocessed_event)

                data[identifier] = preprocessed_event

                if (n_events) % 10 == 0:
                    logging.warning(' finished {} events'.format(n_events))

                if (n_events) % config.N_EVENTS == 0:
                    return data
        return data


if __name__ == '__main__':
    event_lookup = []
    model = load_german_tagger()

    event_data = load_data()
    clean_data = get_preprocessed_events(event_data, model)
    np.save('../data/processed_data.npy', clean_data)
    np.save('../data/event_lookup.npy', event_lookup)
