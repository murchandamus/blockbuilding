import json
from itertools import chain, combinations


class Transaction():
    def __init__(self, txid, fee, weight, parents=[], descendants=[]):
        self.txid = txid
        self.fee = int(fee)
        self.weight = int(weight)
        self.descendants = descendants
        self.parents = parents

    def getLocalClusterTxids(self):
        return list(set([self.txid] + self.descendants + self.parents))

    def __str__(self):
        return "{txid: " + self.txid
        + ", descendants: " + str(self.descendants)
        + ", parents: " + str(self.parents) + "}"


# A set of transactions that forms a unit and may be added to a block as is
class CandidateSet():
    def __init__(self, txs):
        self.txs = {}
        if len(txs) < 1:
            raise TypeError("set cannot be empty")
        for txid, tx in txs.items():
            for p in tx.parents:
                if p not in txs.keys():
                    raise TypeError("parent " + str(p) + " of " + txid + " is not in txs")
        for txid, tx in txs.items():
            self.txs[txid] = tx

    def getWeight(self):
        return sum(tx.weight for tx in self.txs.values())

    def getFees(self):
        return sum(tx.fee for tx in self.txs.values())

    def getEffectiveFeerate(self):
        return self.getFees()/self.getWeight()


# Maximal connected sets of transactions
class Cluster():
    def __init__(self, tx):
        self.representative = tx.txid
        self.txs = {tx.txid: tx}
        self.candidates = []

    def addTx(self, tx):
        self.txs[tx.txid] = tx
        self.representative = min(tx.txid, self.representative)

    def __str__(self):
        return "{" + self.representative + ": " + str(self.txs.keys()) + "}"

    def generateAllCandidateSets(self):
        s = self.txs.values()
        sets = chain.from_iterable(combinations(s, r) for r in range(len(s)+1))
        for candSet in sets:
            try:
                tDict = {}
                for t in candSet:
                    tDict[t.txid] = t
                self.candidates.append(CandidateSet(tDict))
            except TypeError:
                pass

    def getBestCandidateSet(self, weightLimit=0):
        self.generateAllCandidateSets()
        self.candidates.sort(key=lambda cand: cand.getEffectiveFeerate())
        if weightLimit > 0:
            self.candidates = list(filter(lambda d: d.getWeight() <= weightLimit, self.candidates))

        return self.candidates[-1]


# The Mempool class represents a transient state of what is available to be used in a blocktemplate
class Mempool():
    def __init__(self):
        self.txs = {}
        self.clusters = {}  # Maps representative txid to cluster
        self.txClusterMap = {}  # Maps txid to its cluster

    def fromDict(self, txDict):
        for txid, tx in txDict.items():
            self.txs[txid] = tx

    def fromJSON(self, filePath):
        txsJSON = {}
        with open(filePath, 'r') as import_file:
            txsJSON = json.load(import_file)

            for txid in txsJSON.keys():
                self.txs[txid] = Transaction(
                    txid,
                    txsJSON[txid]["fees"]["base"],
                    txsJSON[txid]["weight"],
                    txsJSON[txid]["depends"],
                    txsJSON[txid]["spentby"]
                )
        import_file.close()

    def fromTXT(self, filePath, SplitBy=" "):
        with open(filePath, 'r') as import_file:
            for line in import_file:
                if 'txid' in line:
                    continue
                line = line.rstrip('\n')
                elements = line.split(SplitBy)
                txid = elements[0]
                # parents are not stored in this file type
                self.txs[txid] = Transaction(txid, int(elements[1]), int(elements[2]), [], elements[3:])
        import_file.close()
        # backfill parents from descendants
        for tx in self.txs.values():
            for d in tx.descendants:
                self.txs[d].parents.append(tx.txid)

    def getTx(self, txid):
        return self.txs[txid]

    def getTxs(self):
        return self.txs

    def cluster(self):
        self.clusters = {}
        self.txClusterMap = {}
        for txid, tx in self.getTxs().items():
            if txid in self.txClusterMap.keys():
                continue
            localCluster = Cluster(tx)
            localClusterTxids = tx.getLocalClusterTxids()
            while len(localClusterTxids) > 0:
                nextTxid = localClusterTxids.pop()
                if nextTxid in localCluster.txs.keys():
                    continue
                nextTx = self.getTx(nextTxid)
                localCluster.addTx(nextTx)
                localClusterTxids += nextTx.getLocalClusterTxids()
            self.clusters[localCluster.representative] = localCluster
            for lct in localCluster.txs.keys():
                self.txClusterMap[lct] = localCluster.representative

        return self.clusters

    def popBestCandidateSet(self, weightLimit=40000000):
        self.cluster()
        # Initialize with all transactions from the first cluster
        bestCandidateSet = CandidateSet(list(self.clusters.values())[0].txs)
        for c in self.clusters.values():
            clusterBest = c.getBestCandidateSet(weightLimit)
            if not bestCandidateSet:
                bestCandidateSet = clusterBest
            else:
                if clusterBest.getEffectiveFeerate() > bestCandidateSet.getEffectiveFeerate():
                    bestCandidateSet = clusterBest
        for txid in bestCandidateSet.txs.keys():
            self.txs.pop(txid)
        return bestCandidateSet


def getRepresentativeTxid(txids):
    txids.sort()
    return txids[0]


if __name__ == '__main__':
    # mempoolFileString = "data/mempool.json"
    # mempoolFileString = "/home/murch/Workspace/blockbuilding/data/mini-mempool.json"
    mempoolFileString = "data/mempoolTXT"
    mempool = Mempool()
    mempool.fromTXT(mempoolFileString, " ")
    # mempool.fromJSON(mempoolFileString)
    clusters = mempool.cluster()
    print(clusters)
