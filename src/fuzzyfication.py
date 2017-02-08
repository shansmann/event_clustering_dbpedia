import numpy as np
import rdflib
from SPARQLWrapper import SPARQLWrapper, JSON
import time
import copy
import logging
import re

logging.basicConfig(level=logging.WARNING)

def clean_string(string, regex=r'[^a-zA-Z\s0-9]+'):
    """
    clean string by removing non chars
    """
    return re.sub(regex, '', string)

def query(query, result_format = "JSON", wrapper = "http://dbpedia.org/sparql"):
    sparql = SPARQLWrapper(wrapper)
    sparql.setQuery(query)
    if result_format == "JSON":
        sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return results["results"]["bindings"]


def parse_sparql_results(result):
    if result:
        tmp = []
        for entry in result:
            #import pdb; pdb.set_trace()
            try:
                tmp.append(entry['result']['value'].split('/')[-1])
            except:
                pass
        return tmp
    else:
        return


def one_hop(word):
    res = []
    for predicate in ['subClassOf', 'broader', 'category']:
        q = create_query(word, predicate)
        try:
            query_res = query(q)
        except:
            time.sleep(5)
            try:
                query_res = query(q)
            except:
                res.append([])
                continue
        result = parse_sparql_results(query_res)
        if result:
            res.append(result)
            time.sleep(0.2)
        else:
            res.append([])
    return res


def create_query(word, predicate):
    if predicate == 'category':
        string = """
                    PREFIX dcterms: <http://purl.org/dc/terms/>

                    SELECT ?result
                    WHERE {
                        <%(word)s> dcterms:subject ?result
                    }
                 """ % {'word': word}
        return string
    if predicate == 'subClassOf':
        string = """
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                    SELECT ?result
                    WHERE {
                      <%(word)s> rdf:type ?o.
                      ?o rdfs:subClassOf ?result
                    }
                 """ % {'word': word}
        return string

    if predicate == 'broader':
        string = """
                    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                    PREFIX dcterms: <http://purl.org/dc/terms/>

                    select ?result
                    WHERE {
                      <%(word)s> dcterms:subject ?o .
                      ?o skos:broader ?result
                    }
                 """ % {'word': word}
        return string

    return string


def prepare_data(event_data):
    data = {}
    for key, resources in event_data.item().items():
        if resources:

            # collect all resources & types from spotlight responses
            res_list = []
            type_list = []

            for resource in resources[0]:
                results = list(resource.values())[0]
                res_list.append(results[0])

                # if types are found:
                if results[1] != '':
                    type_list.append(results[1])

            data[key] = {'resources': res_list, 'types': type_list}

        else:
            continue
    return data


def enrich_data(proc_data):

    logging.warning(' events found: {}'.format(len(proc_data.items())))

    n_req = 0

    for i, (key, value) in enumerate(proc_data.items()):

        resources = value['resources']

        n_req += len(resources)

        subClassOf = []
        broader = []
        categories = []

        for entry in resources:
            #import pdb; pdb.set_trace()
            results = one_hop(entry)
            subClassOf.append([clean_string(x) for x in results[0]])
            broader.append([clean_string(x) for x in results[1]])
            categories.append([clean_string(x) for x in results[2]])

        proc_data[key]['subClassOf'] = list(set([item for sublist in subClassOf for item in sublist]))
        proc_data[key]['broader'] = list(set([item for sublist in broader for item in sublist]))
        proc_data[key]['categories'] = list(set([item for sublist in categories for item in sublist]))
        proc_data[key]['resources'] = [clean_string(x.split('/')[-1]) for x in proc_data[key]['resources']]
        proc_data[key]['types'] = [clean_string(x.split('/')[-1]) for x in proc_data[key]['types']]

        if (i + 1) % 10 == 0:
            logging.warning(' finished {} requests'.format(n_req))
            n_req = 0

    return proc_data


if __name__ == '__main__':
    path = '../data/spotlight_responses.npy'
    data = np.load(path)
    processed_data = prepare_data(data)
    expanded_data = enrich_data(processed_data)
    np.save('../data/eventclouds.npy', expanded_data)
