import blockbuilder
import networkx
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


def drawClusterGraph(cluster):
    G = networkx.DiGraph()
    for tx in cluster.txs:
        G.add_node(mempool.txs[tx].txid)
        for parent in mempool.txs[tx].parents:
            G.add_edge(mempool.txs[tx].txid, mempool.txs[parent].txid)
    nodeClr = [mempool.txs[tx].weight for tx in G.nodes()]
    nodeSize = [mempool.txs[tx].weight*10 for tx in G.nodes()]
    print(nodeClr)
    plt.title("graph")
    networkx.draw(G, with_labels=True, node_color=nodeClr, node_size=nodeSize)
    plt.show()


if __name__== "__main__":
    mempool = blockbuilder.Mempool()
    mempool.fromTXT(r"./data/data example/123.mempool")
    cluster_to_check = readCluster(r"./data/data example/123_cluster_example")
    print(cluster_to_check)
    drawClusterGraph(cluster_to_check)