import pandas as pd
import networkx as nx
import string
import re
import matplotlib.pyplot as plt
import graphtools
from textmetrics import calculatePrevalence

from collections import Counter


def load_df_for_texts(path, text_col):
    """Loads csv file from path."""
    df = pd.read_csv(path, index_col=0, parse_dates=["Date"])
    df = df.drop_duplicates(subset=text_col)
    print("Anzahl Mails:", len(df))
    return df


def filter_person(df, person):
    """Filters DataFrame for E-Mail Exchange between given addresses."""
    result = pd.DataFrame(columns=df.columns)
    for pers1 in person:
        for pers2 in person:
            if pers1 != pers2:
                mails = df[(df["From"] == pers1) & (df["To"] == pers2)]
                result = result.append(mails)
    return result


def clean_texts(texts, stopwords, **kwargs):
    """
    Applies cleaning steps on texts.
    texts is a list of strings, one for each e-mail analyzed.
    """
    # Define stopwords
    stopw = list(stopwords) + ["‘"]

    print("Convert to lowercase")
    texts = [t.lower() for t in texts]

    print("Remove words that start with HTTP")
    texts = [re.sub(r"http\S+", " ", t) for t in texts]

    print("Remove words that start with WWW")
    texts = [re.sub(r"www\S+", " ", t) for t in texts]

    print("Remove punctuation")
    regex = re.compile("[%s]" % re.escape(string.punctuation))
    texts = [regex.sub(" ", t) for t in texts]

    print("Remove words made of single letters")
    texts = [re.sub(r"\b\w{1}\b", " ", t) for t in texts]

    print("Remove stopwords")
    pattern = re.compile(r"\b(" + r"|".join(stopw) + r")\b\s*")
    texts = [pattern.sub(" ", t) for t in texts]

    print("Remove additional whitespaces")
    texts = [re.sub(" +", " ", t) for t in texts]

    print("Remove Linebreaks")
    texts = [t.replace("\n", "") for t in texts]

    print("Tokenize text documents (becomes a list of lists)")
    texts = [t.split() for t in texts]

    stemmer = kwargs.get("stemmer", None)
    if stemmer:
        print("Stemming")
        texts = [[stemmer.stem(w) for w in t] for t in texts]

    return texts


def create_wcn(texts, co_range=0, link_filter=2, remove_isolates=False):
    """Creates Word Co-Occurrence Graph from texts."""
    # Create an undirected Network Graph
    G = nx.Graph()

    # Each word is a network node
    prevalence = calculatePrevalence(texts)

    for word in prevalence.keys():
        G.add_node(word, prevalence=prevalence[word])

    # Add links based on co-occurrences
    for doc in texts:
        w_list = []
        length = len(doc)

        if co_range == 0:
            co_range = length  # Betrachtung der gesamten Mail

        for k, w in enumerate(doc):
            # Define range, based on document length
            if (k + co_range) >= length:
                superior = length
            else:
                superior = k + co_range + 1
            # Create the list of co-occurring words
            if k < length - 1:
                for i in range(k + 1, superior):
                    linked_word = doc[i].split()
                    w_list = w_list + linked_word
            # If the list is not empty, create the network links
            if w_list:
                for p in w_list:
                    if G.has_edge(w, p):
                        G[w][p]["weight"] += 1
                    else:
                        G.add_edge(w, p, weight=1)
            w_list = []

    # Create a new Graph which has only links above
    # the minimum co-occurrence threshold
    G_filtered = nx.Graph()
    G_filtered.add_nodes_from(G.nodes(data=True))
    for u, v, data in G.edges(data=True):
        if data["weight"] >= link_filter:
            G_filtered.add_edge(u, v, weight=data["weight"])

    if remove_isolates:
        print("No. of Nodes:", G_filtered.number_of_nodes(), "No. of Edges:", G_filtered.number_of_edges())
        return G_filtered

    # Optional removal of isolates
    isolates = set(nx.isolates(G_filtered))

    G_filtered.remove_nodes_from(isolates)

    # Check the resulting graph (for small test graphs)
    print("Original Network\nNo. of Nodes:", G.number_of_nodes(), "No. of Edges:", G.number_of_edges())
    print("Filtered Network\nNo. of Nodes:", G_filtered.number_of_nodes(), "No. of Edges:", G_filtered.number_of_edges())
    return G_filtered


def show_ego_of_word(G, node, radius=1, min_weight=1, figsize=(20, 15)):
    """Visualizes the ego graph of **node** in **G**."""
    ego = nx.ego_graph(G, node, radius=radius, center=True, undirected=False)
    ego.remove_edges_from(nx.selfloop_edges(ego))

    # Falls man nochmal Filtern will
    if min_weight > 1:
        ego.remove_edges_from([(u, v, d) for u, v, d in ego.edges(data=True) if d["weight"] < min_weight])
        component = nx.node_connected_component(ego, node)
        to_remove = component.symmetric_difference(set(G.nodes))
        ego.remove_nodes_from(to_remove)

    print("No. of Nodes:", ego.number_of_nodes(), "No. of Edges:", ego.number_of_edges())
    colors = graphtools.color_nodes(G=ego, ego_node=node)
    plt.figure(figsize=figsize)
    pos = nx.spring_layout(ego, seed=42, weight="weight")
    labels = nx.draw_networkx_labels(ego, pos=pos, font_color="black")
    edges = nx.draw_networkx_edges(ego, pos=pos, alpha=0.5)

    nx.draw(ego, pos=pos, node_color=colors, edge_color="black", node_size=[50 * oc for d in ego.nodes() for oc in dict(ego.nodes(data=True))[d].values()])
    plt.show()
