import json
import math
import datetime
from itertools import chain, combinations

class Blockbuilder():
    def __init__(self, mempool):
        self.mempool = mempool
        self.selectedTxs = {}
        # 4M weight units minus header of 80 bytes
        self.availableWeight = 4000000-4*80

    def buildBlockTemplate(self):
        while len(self.mempool.txs) > 0 and self.availableWeight > 0:
            bestCandidateSet = self.mempool.popBestCandidateSet(self.availableWeight)
            if bestCandidateSet is None or len(bestCandidateSet.txs) == 0:
                break
            for tx in bestCandidateSet.txs.values():
                self.selectedTxs[tx.txid] = tx
            self.availableWeight -= bestCandidateSet.getWeight()
        return self.selectedTxs

    def outputBlockTemplate(self, blockId=""):
        filePath = "results/"
        if blockId != "":
            filePath += blockId
        else:
            date_now = datetime.datetime.now()
            filePath += date_now.isoformat()

        filePath += '.byclusters'
        with open(filePath, 'w') as output_file:
            selected = CandidateSet(self.selectedTxs)
            output_file.write('CreateNewBlockByClusters(): fees ' + str(selected.getFees()) + ' weight ' + str(selected.getWeight()) + '\n')

            for tx in self.selectedTxs.values():
                output_file.write(tx.txid + '\n')
        output_file.close()


class Transaction():
    def __init__(self, txid, fee, weight, parents=[], descendants=[]):
        self.txid = txid
        self.fee = int(fee)
        self.weight = int(weight)
        self.descendants = descendants
        self.parents = parents

    def getEffectiveFeerate(self):
        return self.fee/self.weight

    def getLocalClusterTxids(self):
        return list(set([self.txid] + self.descendants + self.parents))

    def __str__(self):
        return "{txid: " + self.txid + ", descendants: " + str(self.descendants) + ", parents: " + str(self.parents) + ", fee: " + str(self.fee) + ", weight: " + str(self.weight) + "}"


# A set of transactions that forms a unit and may be added to a block as is
class CandidateSet():
    def __init__(self, txs):
        self.txs = {}
        if len(txs) < 1:
            raise TypeError("set cannot be empty")
        for txid, tx in txs.items():
            if all(parent in txs.keys() for parent in tx.parents):
                self.txs[txid] = tx
            else:
                raise TypeError("parent of " + txid + " is not in txs")

    def __repr__(self):
        return "CandidateSet(%s, %s)" % (str(list(self.txs.keys())), str(self.getEffectiveFeerate()))

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, CandidateSet):
            return self.txs == other.txs
        return NotImplemented

    def getWeight(self):
        return sum(tx.weight for tx in self.txs.values())

    def getFees(self):
        return sum(tx.fee for tx in self.txs.values())

    def getEffectiveFeerate(self):
        return self.getFees()/self.getWeight()

    def getDirectDescendants(self):
        allDirectDescendants = []
        for tx in self.txs.values():
            for d in tx.descendants:
                if d not in self.txs.keys():
                    allDirectDescendants.append(d)
        return allDirectDescendants

    def __str__(self):
        return "{feerate: " + str(self.getEffectiveFeerate()) + ", txs: "+ str(list(self.txs.keys())) + "}" 


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

    def expandCandidateSet(self, candidateSet):
        allDirectDescendants = candidateSet.getDirectDescendants()
        expandedCandidateSets = []
        currentFeerate = candidateSet.getEffectiveFeerate()
        for d in allDirectDescendants:
            # Skip descendants of lower feerate than candidate set without children
            descendant = self.txs[d]
            descendantFeeRate = descendant.getEffectiveFeerate()
            if len(descendant.descendants) == 0 and descendantFeeRate < currentFeerate:
                continue
            addedTxs = {descendant.txid: descendant}
            # collect all necessary ancestors
            incompleteAncestry = descendant.parents
            while len(incompleteAncestry) > 0:
                parentTxid = incompleteAncestry.pop()
                if parentTxid not in candidateSet.txs.keys():
                    parent = self.txs[parentTxid]
                    addedTxs[parent.txid] = parent
                    incompleteAncestry += parent.parents
            addedTxs.update(candidateSet.txs)
            descendantCS = CandidateSet(addedTxs)
            expandedCandidateSets.append(descendantCS)
        return expandedCandidateSets

    def generateAllCandidateSets(self):
        self.candidates = []
        expandedCandidateSets = []
        searchList = []
        ancestorlessTxs = [tx for tx in self.txs.values() if len(tx.parents) == 0]
        for tx in ancestorlessTxs:
            searchList.append(CandidateSet({tx.txid: tx}))

        while len(searchList) > 0:
            nextCS = searchList.pop()
            if nextCS is None or len(nextCS.txs) == 0 or any(nextCS == x for x in expandedCandidateSets):
                pass
            else:
                self.candidates.append(nextCS)
                expandedCandidateSets.append(nextCS)
                searchCandidates = self.expandCandidateSet(nextCS)
                for sc in searchCandidates:
                    if any(sc == x for x in expandedCandidateSets):
                        pass
                    else:
                        searchList.append(sc)
        self.candidates = list(set(self.candidates))

    def getBestCandidateSet(self, weightLimit=0):
        self.generateAllCandidateSets()
        self.candidates.sort(key=lambda cand: cand.getEffectiveFeerate())
        if weightLimit > 0:
            self.candidates = list(filter(lambda d: d.getWeight() <= weightLimit, self.candidates))

        # TODO: will throw on empty
        if len(self.candidates) == 0:
            raise Exception('empty candidate set')
        return self.candidates[-1]

    def removeCandidateSetLinks(self, candidateSet):
        for tx in self.txs.values():
            tx.parents = [t for t in tx.parents if t not in candidateSet.txs.keys()]


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
                    txsJSON[txid]["fee"] * math.pow(10,8),
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
                # descendants are not stored in this file type
                self.txs[txid] = Transaction(txid, int(elements[1]), int(elements[2]), [], elements[3:])
        import_file.close()
        # backfill descendants from parents
        for tx in self.txs.values():
            for p in tx.parents:
                self.txs[p].descendants.append(tx.txid)

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

        print('finished cluster building')
        return self.clusters

    def popBestCandidateSet(self, weightLimit=40000000):
        self.cluster()
        # Initialize with all transactions from the first cluster
        bestCandidateSet = None
        bestCluster = None
        for c in self.clusters.values():
            clusterBest = c.getBestCandidateSet(weightLimit)
            if bestCandidateSet is None:
                bestCandidateSet = clusterBest
                bestCluster = c
            else:
                if clusterBest is None:
                    raise Exception('clusterBest should be defined')
                if clusterBest.getEffectiveFeerate() > bestCandidateSet.getEffectiveFeerate():
                    print ("found better cluster")
                    bestCandidateSet = clusterBest
                    print (str(bestCandidateSet))
                    bestCluster = c

        print('traversed all clusters in popBest')
        bestCluster.removeCandidateSetLinks(bestCandidateSet)
        for txid in bestCandidateSet.txs.keys():
            self.txs.pop(txid)

        # delete modified cluster for recreation next round
        self.clusters.pop(bestCluster.representative)

        print(str(list(bestCandidateSet.txs.keys())))
        return bestCandidateSet


def getRepresentativeTxid(txids):
    txids.sort()
    return txids[0]


if __name__ == '__main__':
    mempool = Mempool()
    mempoolFileString = "data/mempool.json"
    mempool.fromJSON(mempoolFileString)
    bb = Blockbuilder(mempool)
    bb.buildBlockTemplate()
    bb.outputBlockTemplate()
