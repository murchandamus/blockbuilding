from mempool import Mempool
from abstract_builder import Blockbuilder
from collections import OrderedDict
from ancestor_set import AncestorSet
from candidateset import CandidateSet

import utils

import logging

import getopt
import heapq
import time
import sys

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

    if mempoolfilepath == '':
        print ('Missing mempool file path: blockbuilder.py -m <mempoolfile>')
        sys.exit(2)

    startTime = time.time()
    mempool = Mempool()
    mempool.fromTXT(mempoolfilepath)
    bb = AncestorSetBlockbuilder(mempool)
    bb.buildBlockTemplate()
    bb.outputBlockTemplate(mempool.blockId)
    endTime = time.time()
    logging.info('Elapsed time: ' + str(endTime - startTime))

class AncestorSetBlockbuilder(Blockbuilder):
    def __init__(self, mempool, weightLimit=3992820):
        self.mempool = mempool
        self.refMempool = Mempool()
        self.refMempool.fromDict(mempool.txs)
        self.selectedTxs = []
        self.availableWeight = weightLimit
        self.weightLimit = weightLimit
        self.ancestorSets = []
        self.txAncestorSetMap = {}

    def initialize_stubs(self):
        for txid, tx in self.mempool.txs.items():
            # Initialize all AncestorSets just with tx itself
            ancestorSet = AncestorSet(tx)
            logging.debug("AncestorSet created: " + str(ancestorSet))
            heapq.heappush(self.ancestorSets, ancestorSet)
            self.txAncestorSetMap[txid] = ancestorSet

    # Update incomplete AncestorSets lazily when relevant
    def backfill_incomplete_ancestor_set(self, ancestor_set):
        logging.debug("backfilling: " + str(ancestor_set))
        if ancestor_set.isComplete:
            raise ValueError("backfill_incomplete_ancestor_set called with complete AncestorSet: " + str(ancestor_set))
        missing_ancestors = []
        for txid in ancestor_set.getAncestorTxids():
            missing_ancestors.append(self.mempool.txs[txid])
        logging.debug("Missing ancestors: " + str(missing_ancestors))
        ancestor_set.update(missing_ancestors)
        heapq.heappush(self.ancestorSets, ancestor_set)

    # Include transactions from selected ancestor set to block template
    def add_to_block(self, ancestor_set):
        if not ancestor_set.isComplete:
            raise ValueError("add_to_block called with incomplete AncestorSet: " + str(ancestor_set))
        txsIdsToAdd = list(ancestor_set.txs.keys())
        logging.debug("txsIdsToAdd: " + str(txsIdsToAdd))
        while len(txsIdsToAdd) > 0:
            for txid in txsIdsToAdd:
                logging.debug("Try adding txid: " + str(txid))
                if set(self.refMempool.txs[txid].same_block_ancestors).issubset(set(self.selectedTxs)):
                    self.selectedTxs.append(txid)
                    txsIdsToAdd.remove(txid)
        self.availableWeight -= ancestor_set.getWeight()

        # remove included txs from mempool and lazy delete their ancestor sets
        for txid in ancestor_set.txs.keys():
            # lazy delete ancestor sets corresponding to included set
            if txid in self.txAncestorSetMap.keys():
                self.txAncestorSetMap[txid].isObsolete = True
            self.mempool.removeConfirmedTx(txid)

    def reset_remaining_descendants(self, ancestor_set):
        remainingDescendants = ancestor_set.getAllDescendants()

        for d in remainingDescendants:
            logging.debug("Stubbing remaining descendant: " + str(d))
            descendantAncestorSet = self.txAncestorSetMap[d]
            if descendantAncestorSet.isComplete:
                # lazy delete and add stub as replacement
                descendantAncestorSet.isObsolete = True
                replacement = AncestorSet(self.mempool.txs[d])
                self.txAncestorSetMap[d] = replacement
                heapq.heappush(self.ancestorSets, replacement)

    def buildBlockTemplate(self):
        logging.info("Building blocktemplate...")
        self.initialize_stubs()

        while(len(self.ancestorSets) > 0):
            bestAncestorSet = heapq.heappop(self.ancestorSets)
            if bestAncestorSet.isObsolete:
                # execute lazy delete
                continue
            elif not bestAncestorSet.isComplete:
                # Update incomplete AncestorSets lazily when they bubble to the top
                self.backfill_incomplete_ancestor_set(bestAncestorSet)
            elif bestAncestorSet.getWeight() > self.availableWeight:
                # complete, but too big: discard
                continue
            else:
                # Add to block
                self.add_to_block(bestAncestorSet)
                self.reset_remaining_descendants(bestAncestorSet)

        return self.selectedTxs

    def outputBlockTemplate(self, blockId="", result_dir="results/"):
        filePath = result_dir
        if blockId is not None and blockId != "":
            filePath += str(blockId) + '-'
        filePath += utils.get_timestamp()

        filePath += '.byancestors'
        with open(filePath, 'w') as output_file:
            logging.debug(self.selectedTxs)
            if len(self.selectedTxs) > 0:
                # TODO: Implement generic transaction set instead of this misuse
                selected = CandidateSet({txid: self.refMempool.txs[txid] for txid in self.selectedTxs})
                output_file.write('CreateNewBlockByAncestors(): fees ' + str(selected.getFees()) +
                                  ' weight ' + str(selected.getWeight()) + ' size limit ' +
                                  str(self.weightLimit) +'\n')
            else:
                output_file.write('CreateNewBlockByAncestors(): fees ' + '0' +
                                  ' weight ' + '0' + ' size limit ' +
                                  str(self.weightLimit) +'\n')

            for tx in self.selectedTxs:
                output_file.write(tx + '\n')
        output_file.close()

if __name__ == '__main__':
    main(sys.argv[1:])
