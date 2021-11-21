import networkx as nx
import matplotlib.pyplot as plt


def getTopNeighbors(G, node, n_neighbors):
    """Calculates the top n neighbors of a node according to its weights"""
    neighbors = {n: G[node][n]["weight"] for n in G[node]}
    result = sorted(neighbors, key=neighbors.get, reverse=True)[:n_neighbors]
    return result


def get_graph(df, person, **kwargs):
    """Returns the Graph Object"""
    edgelist = create_edgelist(df=df)

    G = nx.Graph()
    G.add_weighted_edges_from(edgelist, weight="weight")
    print("Number of Nodes:", G.number_of_nodes())
    print("Number of Edges:", G.number_of_edges())

    ego_radius = kwargs.get("ego_radius", None)
    if ego_radius:
        G = nx.ego_graph(G, person, radius=ego_radius)

    return G


def plot_graph(G, person, fig_size):
    """Plots the Graph G and marks the Node 'person' and his Egonet."""
    plt.figure(figsize=fig_size)

    colors = color_nodes(G, person)

    pos = nx.spring_layout(G)
    nx.draw(G, pos=pos, node_color=colors, node_size=300.0)


def color_nodes(G, ego_node):
    """Returns a list of colors to plot **G**. Marks **person** and its neighbors in **G**."""
    colors = ["lightblue" for i in range(len(G.nodes))]

    for ind, node in enumerate(G.nodes):
        if node in nx.ego_graph(G, ego_node).nodes:
            colors[ind] = "lightgreen"
        if node == ego_node:
            colors[ind] = "lightcoral"
    return colors


def create_edgelist(df):
    """Creates an edgelist from the given DataFrame."""
    df["weight"] = 1 / df["n_recipients"]
    df_edgelist = df.groupby(["From", "To"]).sum().reset_index()[["From", "To", "weight"]]
    edgelist = list(zip(df_edgelist.From, df_edgelist.To, df_edgelist.weight))
    return edgelist
