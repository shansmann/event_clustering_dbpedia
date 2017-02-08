"""
this script queries dbpedia spotlight for preprocessed data
@TODO: Handle failed requests
"""

import spotlight
import numpy as np
import time
import logging

import config

logging.basicConfig(level=logging.WARNING)

def get_event_entry(data):
    """
    generator to iterate over events
    """

    logging.warning(' {} events found'.format(len(data.item().items())))

    for key, value in data.item().items():
        yield (key, value)


def get_spotlight_responses(event_data):
    data = {}
    failed = []
    for i, (key, value) in enumerate(get_event_entry(event_data)):

        relevant_entries = []

        # concat words
        text = ' '.join(value)

        # query spotlight
        query = query_spotlight(key, text, failed)

        # request succesful
        if query[0]:
            relevant_entries.append(query[1])
        else:
            pass

        data[key] = relevant_entries

        # log progress
        if (i+1) % 10 == 0:
            logging.warning(' finished {} requests'.format(i + 1))
            logging.warning(' # failed req: {}'.format(len(failed)))

    print('----------------failed-----------------')
    time.sleep(2)
    for key, text in failed:

        query = query_spotlight(key, text)

        # request succesful
        if query[0]:
            data[key] = query[1]
        else:
            logging.warning(' no annotations found')
            continue

    return data

def query_spotlight(key, text, failed=[]):
    try:
        res = spotlight.annotate(config.SPOTLIGHT_URL, text, confidence=config.CONFIDENCE, support=config.SUPPORT)
        time.sleep(config.API_LIMIT)
    except:
        res = False
        time.sleep(config.API_LIMIT)
        failed.append((key, text))

    if res:
        relevant = []
        for entry in res:
            # for now only take found resources
            #rel = entry['URI']

            # for multiple fields from res
            rel = {entry['surfaceForm']: [entry[x] for x in config.RELEVANT_SPOTLIGHTS]}
            relevant.append(rel)
        return (True, relevant)
    else:
        return (False, [])

if __name__ == '__main__':
    data = np.load('../data/processed_data.npy')
    np.save('../data/spotlight_responses', get_spotlight_responses(data))
