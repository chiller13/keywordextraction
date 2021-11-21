import numpy as np
import pandas as pd
import networkx as nx
import graphmetrics
from collections import Counter
from distinctiveness.dc import distinctiveness


def calculateTextMetrics(G, tokenized_texts, parallel=True):
    prevalence = calculatePrevalence(texts=tokenized_texts)
    diversity = calculateDiversity(G=G, reverse=False)
    connectivity = calculateConnectivity(G=G, parallel=parallel)

    metrics = pd.DataFrame.from_dict(prevalence, orient="index", columns=["prevalence"])
    metrics["diversity"] = metrics.index.map(diversity)
    metrics["connectivity"] = metrics.index.map(connectivity)

    return metrics


def calculatePrevalence(texts, reverse=True):
    # Create a dictionary with frequency counts for each word
    countPR = Counter()
    for t in texts:
        countPR.update(Counter(t))

    # Calculate average score and standard deviation
    avgPR = np.mean(list(countPR.values()))
    stdPR = np.std(list(countPR.values()))

    # Calculate standardized Prevalence for each keyword
    prevalence = {}
    for t in texts:
        for kw in t:
            prevalence[kw] = (countPR[kw] - avgPR) / stdPR

    sortedPrevalence = {k: v for k, v in sorted(prevalence.items(), key=lambda item: item[1], reverse=reverse)}

    return sortedPrevalence


def calculateDiversity(G, reverse=True):
    # Calculate Distinctiveness Centrality
    DC = distinctiveness(G, normalize=False, alpha=2)
    DIVERSITY_sequence = DC["D2"]

    # Calculate average score and standard deviation
    avgDI = np.mean(list(DIVERSITY_sequence.values()))
    stdDI = np.std(list(DIVERSITY_sequence.values()))
    # Calculate standardized Diversity for each brand
    diversity = {}
    for kw in G.nodes:
        diversity[kw] = (DIVERSITY_sequence[kw] - avgDI) / stdDI

    sortedDiversity = {k: v for k, v in sorted(diversity.items(), key=lambda item: item[1], reverse=reverse)}

    return sortedDiversity


def calculateConnectivity(G, parallel=True, reverse=True):
    # Define inverse weights, beacaus bc interprets weight as distance
    for u, v, data in G.edges(data=True):
        if "weight" in data and data["weight"] != 0:
            data["inverse"] = 1 / data["weight"]
        else:
            data["inverse"] = 1

    if parallel:
        CONNECTIVITY_sequence = graphmetrics.betweenness_centrality_parallel(G, normalized=False, weight="inverse")
    else:
        CONNECTIVITY_sequence = nx.betweenness_centrality(G, normalized=False, weight="inverse")

    # Calculate average score and standard deviation
    avgCO = np.mean(list(CONNECTIVITY_sequence.values()))
    stdCO = np.std(list(CONNECTIVITY_sequence.values()))
    # Calculate standardized Prevalence for each brand
    connectivity = {}
    for kw in G.nodes:
        connectivity[kw] = (CONNECTIVITY_sequence[kw] - avgCO) / stdCO

    sortedConnectivity = {k: v for k, v in sorted(connectivity.items(), key=lambda item: item[1], reverse=reverse)}

    return sortedConnectivity
