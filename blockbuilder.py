from itertools import chain, combinations
import datetime
import getopt
import heapq
import json
import math
from pathlib import Path
import sys
import time

def main(argv):
    mempoolfilepath = ''
    try:
        opts, args = getopt.getopt(argv, "hm:", ["mempoolfile="])
    except getopt.GetoptError:
        print ('blockbuilder.py -m <mempoolfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('blockbuilder.py -m <mempoolfile>')
            sys.exit()
        elif opt in ("-m", "--mempoolfile"):
            mempoolfilepath = arg
        print ('Mempool file is "', mempoolfilepath)

    if mempoolfilepath is '':
        print ('Missing mempool file path: blockbuilder.py -m <mempoolfile>')
        sys.exit(2)

    startTime = time.time()
    mempool = Mempool()
    mempool.fromTXT(mempoolfilepath)
    bb = Blockbuilder(mempool)
    bb.buildBlockTemplate()
    bb.outputBlockTemplate(mempool.blockId)
    endTime = time.time()
    print('Elapsed time: ' + str(endTime - startTime))

class Blockbuilder():
    def __init__(self, mempool):
        self.mempool = mempool
        self.refMempool = Mempool()
        self.refMempool.fromDict(mempool.txs)
        self.selectedTxs = []
        # 4M weight units minus header of 80 bytes
        self.availableWeight = 4000000-4*80

    def buildBlockTemplate(self):
        print("Building blocktemplate…")
        while len(self.mempool.txs) > 0 and self.availableWeight > 0:
            print("Weight left: " + str(self.availableWeight))
            bestCandidateSet = self.mempool.popBestCandidateSet(self.availableWeight)
            if bestCandidateSet is None or len(bestCandidateSet.txs) == 0:
                break
            txsIdsToAdd = list(bestCandidateSet.txs.keys())
            while len(txsIdsToAdd) != 0:
                for txid in txsIdsToAdd:
                    if set(self.refMempool.txs[txid].parents).issubset(set(self.selectedTxs)):
                        self.selectedTxs.append(bestCandidateSet.txs[txid].txid)
                        txsIdsToAdd.remove(txid)
            self.availableWeight -= bestCandidateSet.getWeight()

        return self.selectedTxs

    def outputBlockTemplate(self, blockId=""):
        filePath = "results/"
        if blockId is not None and blockId != "":
            filePath += blockId + '-'
        date_now = datetime.datetime.now()
        filePath += date_now.isoformat()

        filePath += '.byclusters'
        with open(filePath, 'w') as output_file:
            print(self.selectedTxs)
            selected = CandidateSet({txid: self.refMempool.txs[txid] for txid in self.selectedTxs})
            output_file.write('CreateNewBlockByClusters(): fees ' + str(selected.getFees()) + ' weight ' + str(selected.getWeight()) + '\n')

            for tx in self.selectedTxs:
                output_file.write(tx + '\n')
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

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)

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
        self.weight = -1
        self.effectiveFeerate = -1
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
        if self.weight < 0:
            self.weight = sum(tx.weight for tx in self.txs.values())
        return self.weight

    def getFees(self):
        return sum(tx.fee for tx in self.txs.values())

    def getEffectiveFeerate(self):
        if self.effectiveFeerate < 0:
            self.effectiveFeerate = self.getFees()/self.getWeight()
        return self.effectiveFeerate

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
    def __init__(self, tx, weightLimit):
        self.representative = tx.txid
        self.txs = {tx.txid: tx}
        self.ancestorSets = None
        self.bestCandidate = None
        self.bestFeerate = tx.getEffectiveFeerate()
        self.weightLimit = weightLimit
        self.eligibleTxs = {tx.txid: tx}
        self.uselessTxs = {}

    def toJSON(self):
        return json.dumps(self.txs, default=lambda o: o.__dict__)

    def export(self):
        filePath = "problemclusters/"
        filePath += str(len(self.txs))
        filePath += "-" + self.representative
        with open(filePath, 'w') as output_file:
            json.dump(self.toJSON(), output_file)
        output_file.close()

    def addTx(self, tx):
        self.txs[tx.txid] = tx
        self.eligibleTxs[tx.txid] = tx
        self.representative = min(tx.txid, self.representative)
        self.bestFeerate = max(self.bestFeerate, tx.getEffectiveFeerate())

    def __lt__(self, other):
        if self.bestFeerate == other.bestFeerate:
            if other.bestCandidate is None:
                return False
            if self.bestCandidate is None:
                return True
            return self.bestCandidate.getWeight() > other.bestCandidate.getWeight()
        return self.bestFeerate > other.bestFeerate

    def __str__(self):
        return "{" + self.representative + ": " + str(self.txs.keys()) + "}"

    # Return CandidateSet composed of txid and its ancestors
    def assembleAncestry(self, txid):
        # cache ancestry until cluster is used
        if self.ancestorSets is None or txid not in self.ancestorSets:
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

    def pruneEligibleTxs(self, bestFeerate):
        while True:
            nothingChanged = True
            prune = []
            for txid, tx in self.eligibleTxs.items():
                if tx.getEffectiveFeerate() >= bestFeerate:
                    continue
                if len(tx.descendants) == 0:
                    # can never be part of best candidate set, due to low feerate and no descendants
                    nothingChanged = False
                    prune.append(txid)
                    self.uselessTxs[txid] = tx
                elif all(d in self.uselessTxs.keys() for d in tx.descendants):
                    # can never be part of best candidate set, due to low feerate and only useless descendants
                    nothingChanged = False
                    prune.append(txid)
                    self.uselessTxs[txid] = tx
            for txid in prune:
                self.eligibleTxs.pop(txid)
            if nothingChanged:
                break

    def expandCandidateSet(self, candidateSet, bestFeerate):
        allDirectDescendants = candidateSet.getDirectDescendants()
        expandedCandidateSets = []
        for d in allDirectDescendants:
            # Skip descendants of lower feerate than candidate set without children
            descendant = self.txs[d]
            descendantFeeRate = descendant.getEffectiveFeerate()
            if d in self.uselessTxs.keys():
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

    def getBestCandidateSet(self, weightLimit):
        self.weightLimit = min(weightLimit, self.weightLimit)
        if self.bestCandidate is not None and self.bestCandidate.getWeight() <= self.weightLimit:
            return self.bestCandidate
        self.eligibleTxs = {}
        self.eligibleTxs.update(self.txs)
        self.uselessTxs = {}
        print("Calculate bestCandidateSet at weightLimit of " + str(weightLimit) + " for cluster of " + str(len(self.txs)) + ": " + str(self))
        if (len(self.txs) > 99):
            self.export()
        bestCand = None # current best candidateSet
        expandedCandidateSets = [] # candidateSets that have been evaluated
        searchList = [] # candidates that still need to be evaluated

        for txid in self.eligibleTxs.keys():
            cand = self.assembleAncestry(txid)
            if cand.getWeight() <= self.weightLimit:
                if bestCand is None or bestCand.getEffectiveFeerate() < cand.getEffectiveFeerate() or (bestCand.getEffectiveFeerate() == cand.getEffectiveFeerate() and bestCand.getWeight() < cand.getWeight()):
                    bestCand = cand
                    print('ancestrySet is new best candidate set in cluster ' + str(bestCand))
                searchList.append(bestCand)

        if bestCand is not None:
            self.pruneEligibleTxs(bestCand.getEffectiveFeerate())
            searchList.append(CandidateSet(self.eligibleTxs))

        while len(searchList) > 0 and len(expandedCandidateSets) < 1000:
            searchList.sort(key=lambda x: x.getEffectiveFeerate())
            nextCS = searchList.pop()
            if nextCS is None or len(nextCS.txs) == 0 or any(nextCS == x for x in expandedCandidateSets):
                pass
            elif nextCS.getWeight() > self.weightLimit:
                expandedCandidateSets.append(nextCS)
            else:
                expandedCandidateSets.append(nextCS)
                if (nextCS.getEffectiveFeerate() > bestCand.getEffectiveFeerate() or (nextCS.getEffectiveFeerate() == bestCand.getEffectiveFeerate() and nextCS.getWeight() > bestCand.getWeight())):
                    bestCand = nextCS
                    self.pruneEligibleTxs(bestCand.getEffectiveFeerate())
                    searchList.append(CandidateSet(self.eligibleTxs))
                searchCandidates = self.expandCandidateSet(nextCS, bestCand.getEffectiveFeerate())
                for sc in searchCandidates:
                    if nextCS.getWeight() > self.weightLimit:
                        pass
                    elif any(sc == x for x in expandedCandidateSets):
                        pass
                    else:
                        searchList.append(sc)
        self.bestCandidate = bestCand
        if bestCand is not None:
            self.bestFeerate = bestCand.getEffectiveFeerate()
        else:
            self.bestFeerate = -1

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
        self.blockId = ''

    def fromDict(self, txDict, blockId = 'dictionary'):
        self.blockId = blockId
        for txid, tx in txDict.items():
            self.txs[txid] = tx
            self.txsToBeClustered[txid] = tx

    def fromJSON(self, filePath):
        txsJSON = {}
        with open(filePath, 'r') as import_file:
            self.blockId = Path(filePath).stem
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
            self.blockId = Path(filePath).stem
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

    def cluster(self, weightLimit):
        for txid, tx in self.txsToBeClustered.items():
            if txid in self.txClusterMap.keys():
                continue
            print("Cluster tx: " + txid)
            localCluster = Cluster(tx, weightLimit)
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
            heapq.heappush(self.clusterHeap, localCluster)

        print('finished cluster building')
        self.txsToBeClustered = {}
        return self.clusters

    def popBestCandidateSet(self, weightLimit):
        print("Called popBestCandidateSet with weightLimit " + str(weightLimit))
        self.cluster(weightLimit)
        bestCluster = heapq.heappop(self.clusterHeap)
        bestCandidateSet = bestCluster.bestCandidate
        # Calculate bestCandidate from heap best, until cluster with eligible candidateSet bubbles to top
        while (bestCandidateSet is None or bestCandidateSet.getWeight() > weightLimit) and len(self.clusterHeap) > 0:
            # Update best candidate set in cluster with weight limit
            if bestCandidateSet is not None:
                print("bestCandidateSet " + str(bestCandidateSet) + " is over weight limit: " + str(weightLimit))
            if bestCluster.getBestCandidateSet(weightLimit) is None:
                # don't add bestCluster without candidateSet back to heap
                bestCluster = heapq.heappop(self.clusterHeap)
            else:
                # add refreshed bestCluster back to heap then get best
                bestCluster = heapq.heappushpop(self.clusterHeap, bestCluster)
            bestCandidateSet = bestCluster.bestCandidate

        if bestCandidateSet is not None and bestCandidateSet.getWeight() > weightLimit:
            bestCandidateSet = None

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
    main(sys.argv[1:])
