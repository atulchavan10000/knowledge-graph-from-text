import wikipedia as wp
import re
import coreferee
import spacy
import networkx as nx
from pyvis.network import Network
import webbrowser

# Load the data
wp.set_lang("en")
title = "Mumbai"
data = wp.page(title).content

# Preprocess the data
data = data.lower().replace("\n", "")
data = re.sub('== see also ==.*|[@#:&\"]|===.*?===|==.*?==|\(.*?\)', '', data)

# Recognize named entities
nlp = spacy.load('en_core_web_lg')
doc = nlp(data)

# Compute coreference clusters
nlp.add_pipe('coreferee')
doc = nlp(data)

# Register the extension attribute 'is_coref'
spacy.tokens.Token.set_extension('is_coref', default=False, force=True)

# Resolve coreferences
resolved_data = " ".join(token.text if not token._.is_coref else token._.coref_resolved for token in doc)

# Extract relationships
def extract_relationship(sentence):
    doc = nlp(sentence)
    first, last = None, None

    for chunk in doc.noun_chunks:
        if not first:
            first = chunk
        else:
            last = chunk

    if first and last:
        return (first.text.strip(), last.text.strip(), str(doc[first.end:last.start]).strip())

    return (None, None, None)

# Create a graph
graph_doc = nlp(resolved_data)
nx_graph = nx.DiGraph()

for sent in enumerate(graph_doc.sents):
    if len(sent[1]) > 3:
        (a, b, c) = extract_relationship(str(sent[1]))

        # Add nodes and edges to graph
        if a and b:
            nx_graph.add_node(a, size=5)
            nx_graph.add_node(b, size=5)
            nx_graph.add_edge(a, b, weight=1, title=c, arrows="to")

# Create a Network object
g = Network(notebook=False, directed=True)

# Add nodes and edges from the graph to the Network object
for node in nx_graph.nodes():
    g.add_node(node, size=nx_graph.nodes[node]['size'])

for edge in nx_graph.edges():
    g.add_edge(edge[0], edge[1], weight=nx_graph.edges[edge]['weight'], title=nx_graph.edges[edge]['title'], arrows=nx_graph.edges[edge]['arrows'])

# Save the Network object to an HTML file
g.save_graph("graph.html")

# Open the HTML file in the default web browser
webbrowser.open("graph.html")

def process_query(graph, query):
    query = query.lower()
    results = []

    # Search for nodes that exactly match the query
    matching_nodes = [node for node in graph.nodes if query == node.lower()]

    # For each matching node, find connected edges and other nodes
    for node in matching_nodes:
        connected_edges = [edge for edge in graph.edges if node in edge]

        for edge in connected_edges:
            other_node = (edge[0] if edge[1] == node else edge[1])

            # Ensure that the edge has a 'title' attribute
            if 'title' in graph.edges[edge]:
                # Construct the statement
                statement = f"{node.capitalize()}  {graph.edges[edge]['title']}  {other_node.capitalize()}"
                results.append(statement)

    return results

# User Query Interface
while True:
    query = input("Enter your query (type 'exit' to quit): ")

    if query.lower() == 'exit':
        break

    # Process the query and find relevant information from the graph
    query_result = process_query(nx_graph, query)
    
    if not query_result:
        print("No information found.")
    else:
        for result in query_result:
            print(result)
