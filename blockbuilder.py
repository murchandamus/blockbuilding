from itertools import chain, combinations
import datetime
import heapq
import json
import math

class Blockbuilder():
    def __init__(self, mempool):
        self.mempool = mempool
        self.selectedTxs = {}
        # 4M weight units minus header of 80 bytes
        self.availableWeight = 4000000-4*80

    def buildBlockTemplate(self):
        print("Building blocktemplate…")
        while len(self.mempool.txs) > 0 and self.availableWeight > 0:
            print("Weight left: " + str(self.availableWeight))
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


# A Transaction in the context of a specific mempool and blocktemplate state.
# Ancestors, Parents, and Descendants will be updated as the blocktemplate is being built whenever anything gets picked from the Cluster.
class Transaction():
    def __init__(self, txid, fee, weight, parents=None, descendants=None):
        self.txid = txid
        self.fee = int(fee)
        self.weight = int(weight)
        if parents is None:
            parents = []
        self.parents = parents
        if descendants is None:
            descendants = []
        self.descendants = descendants

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
        self.ancestorSets = None
        self.bestCandidate = None

    def addTx(self, tx):
        self.txs[tx.txid] = tx
        self.representative = min(tx.txid, self.representative)

    def __lt__(self, other):
        if self.bestCandidate is None:
            print('Cluster ' + str(self) + 'has no CandidateSet')
        myCandidate = self.getBestCandidateSet()
        if myCandidate is None:
            return false
        myWeight = myCandidate.getWeight()
        myFeeRate = myCandidate.getEffectiveFeerate()

        otherCandidate = other.getBestCandidateSet()
        otherWeight = otherCandidate.getWeight()
        otherFeeRate = otherCandidate.getEffectiveFeerate()
        return myFeeRate > otherFeeRate or (myFeeRate == otherFeeRate and myWeight > otherWeight)

    def __str__(self):
        return "{" + self.representative + ": " + str(self.txs.keys()) + "}"

    # Return CandidateSet composed of txid and its ancestors
    def assembleAncestry(self, txid):
        # cache ancestry until cluster is used
        if self.ancestorSets is not None and txid in self.ancestorSets:
            return self.ancestorSets[txid]

        # collect all ancestors of txid
        tx = self.txs[txid]
        ancestry = {txid: tx}
        searchList = [] + tx.parents
        while len(searchList) > 0:
            ancestorTxid = searchList.pop()
            if ancestorTxid not in ancestry.keys():
                ancestor = self.txs[ancestorTxid]
                ancestry[ancestorTxid] = ancestor
                searchList += ancestor.parents
        ancestorSet = CandidateSet(ancestry)
        if self.ancestorSets is None:
            self.ancestorSets = {txid: ancestorSet}
        else:
            self.ancestorSets[txid] = ancestorSet
        return self.ancestorSets[txid]

    def expandCandidateSet(self, candidateSet, bestFeerate):
        allDirectDescendants = candidateSet.getDirectDescendants()
        expandedCandidateSets = []
        for d in allDirectDescendants:
            # Skip descendants of lower feerate than candidate set without children
            descendant = self.txs[d]
            descendantFeeRate = descendant.getEffectiveFeerate()
            if len(descendant.descendants) == 0 and descendantFeeRate < bestFeerate:
                continue
            # Ensure this is a new dictionary instead of modifying an existing
            expandedSetTxs = {descendant.txid: descendant}
            # Add ancestry
            expandedSetTxs.update(self.assembleAncestry(descendant.txid).txs)
            # Add previous CandidateSet
            expandedSetTxs.update(candidateSet.txs)
            descendantCS = CandidateSet(expandedSetTxs)
            expandedCandidateSets.append(descendantCS)
        return expandedCandidateSets

    def getBestCandidateSet(self, weightLimit=4000000):
        if self.bestCandidate is not None and self.bestCandidate.getWeight() <= weightLimit:
            return self.bestCandidate
        print("Calculate bestCandidateSet for cluster of " + str(len(self.txs)) + ": " + str(self))
        bestCand = None # current best candidateSet
        expandedCandidateSets = [] # candidateSets that have been evaluated
        searchList = [] # candidates that still need to be evaluated
        ancestorlessTxs = [tx for tx in self.txs.values() if len(tx.parents) == 0]
        for tx in ancestorlessTxs:
            cand = CandidateSet({tx.txid: tx})
            if tx.weight <= weightLimit:
                if bestCand is None or bestCand.getEffectiveFeerate() < cand.getEffectiveFeerate():
                    bestCand = cand
                searchList.append(cand)

        while len(searchList) > 0:
            searchList.sort(key=lambda x: x.getEffectiveFeerate())
            nextCS = searchList.pop()
            if nextCS is None or len(nextCS.txs) == 0 or any(nextCS == x for x in expandedCandidateSets):
                pass
            elif nextCS.getWeight() > weightLimit:
                pass
            else:
                expandedCandidateSets.append(nextCS)
                if (nextCS.getEffectiveFeerate() > bestCand.getEffectiveFeerate()):
                    bestCand = nextCS
                searchCandidates = self.expandCandidateSet(nextCS, bestCand.getEffectiveFeerate())
                for sc in searchCandidates:
                    if nextCS.getWeight() > weightLimit:
                        pass
                    elif any(sc == x for x in expandedCandidateSets):
                        pass
                    else:
                        searchList.append(sc)
        self.bestCandidate = bestCand

        return self.bestCandidate

    def removeCandidateSetLinks(self, candidateSet):
        for tx in self.txs.values():
            tx.parents = [t for t in tx.parents if t not in candidateSet.txs.keys()]
            tx.descendants = [t for t in tx.descendants if t not in candidateSet.txs.keys()]


# The Mempool class represents a transient state of what is available to be used in a blocktemplate
class Mempool():
    def __init__(self):
        self.txs = {}
        self.txsToBeClustered = {} # Bucket for transactions from used cluster
        self.clusters = {}  # Maps representative txid to cluster
        self.clusterHeap = [] # Heapifies clusters by bestCandidateSet
        self.txClusterMap = {}  # Maps txid to its cluster

    def fromDict(self, txDict):
        for txid, tx in txDict.items():
            self.txs[txid] = tx
            self.txsToBeClustered[txid] = tx

    def fromJSON(self, filePath):
        txsJSON = {}
        with open(filePath, 'r') as import_file:
            txsJSON = json.load(import_file)

            for txid in txsJSON.keys():
                tx = Transaction(
                    txid,
                    txsJSON[txid]["fee"] * math.pow(10,8),
                    txsJSON[txid]["weight"],
                    txsJSON[txid]["depends"],
                    txsJSON[txid]["spentby"]
                )
                self.txs[txid] = tx
                self.txsToBeClustered[txid] = tx
        import_file.close()

    def fromTXT(self, filePath, SplitBy=" "):
        print("Loading mempool…")
        with open(filePath, 'r') as import_file:
            for line in import_file:
                if 'txid' in line:
                    continue
                line = line.rstrip('\n')
                elements = line.split(SplitBy)
                txid = elements[0]
                # descendants are not stored in this file type
                tx = Transaction(txid, int(elements[1]), int(elements[2]), elements[3:])
                self.txs[txid] = tx
                self.txsToBeClustered[txid] = tx
        import_file.close()
        print("Mempool loaded")
        # backfill descendants from parents
        print("Backfill descendants from parents…")
        for tx in self.txs.values():
            for p in tx.parents:
                self.txs[p].descendants.append(tx.txid)
        print("Descendants backfilled")

    def getTx(self, txid):
        return self.txs[txid]

    def getTxs(self):
        return self.txs

    def cluster(self, weightLimit=4000000):
        for txid, tx in self.txsToBeClustered.items():
            if txid in self.txClusterMap.keys():
                continue
            print("Cluster tx: " + txid)
            localCluster = Cluster(tx)
            localClusterTxids = tx.getLocalClusterTxids()
            while len(localClusterTxids) > 0:
                nextTxid = localClusterTxids.pop()
                if nextTxid in localCluster.txs.keys():
                    continue
                nextTx = self.getTx(nextTxid)
                localCluster.addTx(nextTx)
                localClusterTxids += nextTx.getLocalClusterTxids()
            localCluster.getBestCandidateSet(weightLimit)
            self.clusters[localCluster.representative] = localCluster
            for lct in localCluster.txs.keys():
                self.txClusterMap[lct] = localCluster.representative
            heapq.heappush(self.clusterHeap, localCluster)

        print('finished cluster building')
        self.txsToBeClustered = {}
        return self.clusters

    def popBestCandidateSet(self, weightLimit=40000000):
        self.cluster(weightLimit)
        bestCluster = heapq.heappop(self.clusterHeap)
        bestCandidateSet = bestCluster.bestCandidate
        if bestCandidateSet is None:
            raise Exception("Best candidate set was None unexpectedly in cluster: " + str(bestCluster))
        # If bestCandidateSet exceeds weightLimit, refresh bestCluster and get next best cluster
        while bestCandidateSet.getWeight() > weightLimit:
            # Update best candidate set in cluster with weight limit
            print("bestCandidateSet " + str(bestCandidateSet) + " is over weight limit: " + str(weightLimit))
            bestCluster.getBestCandidateSet(weightLimit)
            bestCluster = heapq.heappushpop(self.clusterHeap, bestCluster)
            bestCandidateSet = bestCluster.bestCandidate

        print("best candidate from all clusters: " + str(bestCandidateSet))

        if bestCandidateSet is None:
            print("Block finished")
        else:
            # delink bestCandidateSet from remaining cluster
            bestCluster.removeCandidateSetLinks(bestCandidateSet)
            # remove cluster mapping for transactions in cluster
            for txid, tx in bestCluster.txs.items():
                self.txClusterMap.pop(txid)
                if txid in bestCandidateSet.txs.keys():
                    # remove bestCandidateSet from mempool
                    self.txs.pop(txid)
                else:
                    # stage other txs for clustering in mempool
                    self.txsToBeClustered[txid] = tx

            # delete modified cluster for recreation next round
            self.clusters.pop(bestCluster.representative)

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
