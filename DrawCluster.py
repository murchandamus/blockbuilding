import blockbuilder
import networkx
from networkx.drawing.nx_agraph import write_dot, graphviz_layout
import matplotlib.pyplot as plt


def readCluster(fileLocation):
    try:
        clusterFile = open(fileLocation, 'r')
        line = clusterFile.readline().strip()
        cluster = blockbuilder.Cluster(mempool.txs[line], 40000)
        line = clusterFile.readline().strip()
        while line:
            print(line)
            cluster.addTx(mempool.txs[line])
            line = clusterFile.readline().strip()
        clusterFile.close()
        return cluster
    except FileNotFoundError:
        print("file not found: "+fileLocation)

def readClusterFromMempool():

    return list(mempool.cluster(4000000).values())[0]


def drawClusterGraph(cluster):
    G = networkx.DiGraph()
    for tx in cluster.txs:
        G.add_node(mempool.txs[tx].txid)
        for parent in mempool.txs[tx].parents:
            G.add_edge(mempool.txs[tx].txid, mempool.txs[parent].txid)
    write_dot(G, 'test.dot')
    plt.title("graph")
    pos = graphviz_layout(G, prog='dot')
    networkx.draw(G, pos, with_labels=False, arrows=True)

    nodeClr = [mempool.txs[tx].weight for tx in G.nodes()]
    nodeSize = [mempool.txs[tx].weight*10 for tx in G.nodes()]
    print(nodeClr)

#    networkx.draw_spring(G, with_labels=False, node_color=nodeClr)
    plt.show()



if __name__== "__main__":
    mempool = blockbuilder.Mempool()
#    mempool.fromTXT(r"./data/data example/000000000000000000067df78658a05f17aea0844d11c1854a740abf8b6b70cb.mempool")
    mempool.fromJSON(r"./problemclusters/128-02606da767bf3bef760ebb312f800ca9022d57c6bb5416872057be8d400cd160")
    cluster = readClusterFromMempool()
    print(type(cluster))
    drawClusterGraph(cluster)

    '''
    cluster_to_check = readCluster(r"./data/data example/123_cluster_example")
    print(cluster_to_check)
    drawClusterGraph(cluster_to_check)'''