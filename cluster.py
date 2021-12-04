import heapq
import json
import logging

from candidateset import CandidateSet

# Maximal connected sets of transactions
class Cluster():
    def __init__(self, tx, weightLimit):
        self.representative = tx.txid
        self.txs = {tx.txid: tx}
        self.ancestorSets = None
        self.bestCandidate = None
        self.bestFeerate = tx.getFeerate()
        self.weightLimit = weightLimit
        self.eligibleTxs = {tx.txid: tx}
        self.uselessTxs = {}

    def createExportDict(self):
        exportDict = {}
        for txid, tx in self.txs.items():
            exportDict[txid] = tx.createExportDict()
        return exportDict

    def export(self):
        filePath = "problemclusters/"
        filePath += str(len(self.txs))
        filePath += "-" + self.representative
        with open(filePath, 'w') as output_file:
            json.dump(self.createExportDict(), output_file, indent=2)
        output_file.close()

    def addTx(self, tx):
        self.txs[tx.txid] = tx
        self.eligibleTxs[tx.txid] = tx
        self.representative = min(tx.txid, self.representative)
        self.bestFeerate = max(self.bestFeerate, tx.getFeerate())

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
        while 1:
            nothingChanged = True
            prune = []
            for txid, tx in self.eligibleTxs.items():
                if tx.getFeerate() >= bestFeerate:
                    continue
                if len(tx.children) == 0:
                    # can never be part of best candidate set, due to low feerate and no children
                    logging.debug(txid + ': useless, too low feerate and no children')
                    nothingChanged = False
                    prune.append(txid)
                    self.uselessTxs[txid] = tx
                elif all(d in self.uselessTxs.keys() for d in tx.children):
                    # can never be part of best candidate set, due to low feerate and only useless descendants
                    logging.debug(txid + ': useless, too low feerate and useless children')
                    nothingChanged = False
                    prune.append(txid)
                    self.uselessTxs[txid] = tx
            for txid in prune:
                self.eligibleTxs.pop(txid)
            if nothingChanged:
                break

    def expandCandidateSet(self, candidateSet, bestFeerate):
        allChildren = candidateSet.getChildren()
        expandedCandidateSets = []
        for d in allChildren:
            if d in self.uselessTxs.keys() or d in candidateSet.txs.keys():
                continue
            # Skip children of lower feerate than candidate set without children
            descendant = self.txs[d]
            descendantFeeRate = descendant.getFeerate()
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
        logging.debug("Calculate bestCandidateSet at weightLimit of " + str(weightLimit) + " for cluster of " + str(len(self.txs)) + ": " + str(self))
        if (len(self.txs) > 99):
            self.export()
        bestCand = None # current best candidateSet
        previouslyEvaluated = set() # candidateSets that have been evaluated
        searchHeap = [] # candidates that still need to be evaluated

        for txid in self.eligibleTxs.keys():
            #TODO: sort transactions by feerate, stop seeding candidate sets when feerate of transaction is smaller than the setfeerate of bestCand
            cand = self.assembleAncestry(txid)
            if cand.getWeight() <= self.weightLimit:
                if bestCand is None or bestCand.getEffectiveFeerate() < cand.getEffectiveFeerate() or (bestCand.getEffectiveFeerate() == cand.getEffectiveFeerate() and bestCand.getWeight() < cand.getWeight()):
                    bestCand = cand
                    logging.debug('ancestrySet is new best candidate set in cluster ' + str(bestCand))
                heapq.heappush(searchHeap, bestCand)

        if bestCand is not None:
            self.pruneEligibleTxs(bestCand.getEffectiveFeerate())
            heapq.heappush(searchHeap, CandidateSet(self.eligibleTxs))

        while len(searchHeap) > 0 and len(previouslyEvaluated) < 1000:
            nextCS = heapq.heappop(searchHeap)
            if nextCS is None or len(nextCS.txs) == 0 or nextCS in previouslyEvaluated:
                pass
            elif nextCS.getWeight() > self.weightLimit:
                previouslyEvaluated.add(nextCS)
            else:
                previouslyEvaluated.add(nextCS)
                if (nextCS.getEffectiveFeerate() > bestCand.getEffectiveFeerate() or (nextCS.getEffectiveFeerate() == bestCand.getEffectiveFeerate() and nextCS.getWeight() > bestCand.getWeight())):
                    bestCand = nextCS
                    logging.debug('new best candidate set in cluster ' + str(bestCand))
                    self.pruneEligibleTxs(bestCand.getEffectiveFeerate())
                    heapq.heappush(searchHeap, CandidateSet(self.eligibleTxs))
                searchCandidates = self.expandCandidateSet(nextCS, bestCand.getEffectiveFeerate())
                for sc in searchCandidates:
                    if nextCS.getWeight() > self.weightLimit:
                        pass
                    elif any(sc == x for x in previouslyEvaluated):
                        pass
                    else:
                        heapq.heappush(searchHeap, sc)
        logging.debug('expanded ' + str(len(previouslyEvaluated)) + ' candidateSets cluster ' + str(self.representative))
        self.bestCandidate = bestCand
        if bestCand is not None:
            self.bestFeerate = bestCand.getEffectiveFeerate()
        else:
            self.bestFeerate = -1

        return self.bestCandidate

    def removeCandidateSetLinks(self, candidateSet):
        for tx in self.txs.values():
            #tx.parents = [t for t in tx.parents if t not in candidateSet.txs.keys()]
            #tx.ancestors = [t for t in tx.ancestors if t not in candidateSet.txs.keys()]
            tx.children = [t for t in tx.children if t not in candidateSet.txs.keys()]
            tx.descendants = [t for t in tx.descendants if t not in candidateSet.txs.keys()]

