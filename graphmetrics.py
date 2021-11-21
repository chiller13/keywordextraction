from multiprocessing import Pool
import itertools
import networkx as nx
import pandas as pd


def _calculate_metrics(G, metrics_dict, graph_metrics):
    """Calculates metrics for the given Griven G."""

    metrics = _calculate_unweighted_metrics(G=G, metrics_dict=metrics_dict["unweighted"], graph_metrics=graph_metrics)
    metrics = _calculate_weighted_metrics(G=G, metrics_dict=metrics_dict["weighted"], graph_metrics=metrics)
    return metrics


def _calculate_personal_metrics(G, metrics_dict, person, graph_metrics):
    """Calculates personal metrics for the given Griven G."""

    metrics = _calculate_personal_unweighted_metrics(G=G, metrics_dict=metrics_dict["unweighted"], graph_metrics=graph_metrics, person=person)
    metrics = _calculate_personal_weighted_metrics(G=G, metrics_dict=metrics_dict["weighted"], graph_metrics=metrics, person=person)
    return metrics


def _calculate_unweighted_metrics(G, metrics_dict, graph_metrics):
    """Calculates unweighted metrics on Graph G."""
    for metric in metrics_dict.keys():
        graph_metrics[str(metric)] = metrics_dict[metric](G)

    return graph_metrics


def _calculate_weighted_metrics(G, metrics_dict, graph_metrics):
    """Calculates weighted metrics on Graph G."""
    for metric in metrics_dict.keys():
        graph_metrics[str(metric)] = metrics_dict[metric](G, weight="weight")

    return graph_metrics


def _calculate_personal_unweighted_metrics(G, metrics_dict, graph_metrics, person):
    """Calculates unweighted metrics on Graph G for person."""
    for metric in metrics_dict.keys():

        if person in G.nodes:
            graph_metrics[str(metric)] = metrics_dict[metric](G)[person]
        else:
            graph_metrics[str(metric)] = 0

    return graph_metrics


def _calculate_personal_weighted_metrics(G, metrics_dict, graph_metrics, person):
    """Calculates unweighted metrics on Graph G for person."""
    for metric in metrics_dict.keys():

        if person in G.nodes:
            graph_metrics[str(metric)] = metrics_dict[metric](G, weight="weight")[person]
        else:
            graph_metrics[str(metric)] = 0

    return graph_metrics


def chunks(l, n):
    """Divide a list of nodes `l` in `n` chunks"""
    l_c = iter(l)
    while 1:
        x = tuple(itertools.islice(l_c, n))
        if not x:
            return
        yield x


def betweenness_centrality_parallel(G, weight, normalized=True, processes=None):
    """Parallel betweenness centrality  function"""
    p = Pool(processes=processes)
    node_divisor = len(p._pool) * 4
    node_chunks = list(chunks(G.nodes(), int(G.order() / node_divisor)))
    num_chunks = len(node_chunks)
    bt_sc = p.starmap(
        nx.betweenness_centrality_subset,
        zip(
            [G] * num_chunks,
            node_chunks,
            [list(G)] * num_chunks,
            [normalized] * num_chunks,
            [weight] * num_chunks,
        ),
    )

    # Reduce the partial solutions
    bt_c = bt_sc[0]
    for bt in bt_sc[1:]:
        for n in bt:
            bt_c[n] += bt[n]
    return bt_c


def get_highest_weight_neighbors(G, person, n_neighbors=3):
    edge_data = sorted(G.edges(person, data=True), key=lambda t: t[2].get("weight", 1), reverse=True)[1 : n_neighbors + 1]

    neighbor_dict = {}

    for contact in edge_data:
        neighbor_dict[contact[1]] = contact[2].get("weight")

    return neighbor_dict


def get_neighbors(highest_neighbors: pd.Series):
    neighbors = {}

    for dic in highest_neighbors:
        for key in dic:
            if key not in neighbors:
                neighbors[key] = dic[key]
            else:
                neighbors[key] += dic[key]

    return {k: v for k, v in sorted(neighbors.items(), key=lambda item: item[1], reverse=True)}


def filter_person(df, pers1, pers2):
    """Filters DataFrame for E-Mail Exchange between given addresses."""
    result = df[(df["From"] == pers1) & (df["To"] == pers2)]

    return result


def get_mails_per_day(df_raw: pd.DataFrame, poi1: str, poi2: str, timeline):
    poi1_to_poi2 = [0] * len(timeline)
    cum_mails = 0

    df = filter_person(df_raw, pers1=poi1, pers2=poi2)
    df = df.groupby([df["Date"].dt.date]).sum()

    for ind, day in enumerate(timeline):
        if day.date() in df.index:
            cum_mails += df[df.index == day.date()]["weight"][0]

        poi1_to_poi2[ind] = cum_mails

    return poi1_to_poi2


def get_weekly_indices(timeline: pd.Series):
    indices = []

    for ind, week in enumerate(timeline):
        if ind % 8 == 0:
            indices.append(ind)

    return indices
