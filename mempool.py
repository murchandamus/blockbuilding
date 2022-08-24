import heapq
import json
import math
import decimal
from pathlib import Path
import logging
import time

from transaction import Transaction


# The Mempool class represents a transient state of what is available to be used in a blocktemplate at a specific height
class Mempool():
    def __init__(self):
        self.txs = {}
        self.blockId = ''


    def fromDict(self, txDict, blockId = 'dictionary'):
        self.blockId = blockId
        for txid, tx in txDict.items():
            self.txs[txid] = tx


    def fromJSON(self, filePath):
        txsJSON = {}
        with open(filePath, 'r') as import_file:
            self.blockId = Path(filePath).stem
            txsJSON = json.load(import_file, parse_float=decimal.Decimal)

            for txid in txsJSON.keys():
                tx = Transaction(
                    txid,
                    txsJSON[txid]["fee"].shift(8),
                    txsJSON[txid]["weight"],
                    txsJSON[txid]["depends"],
                    txsJSON[txid]["spentby"]
                )
                self.txs[txid] = tx
        import_file.close()


    def fromTXT(self, filePath, SplitBy=" "):
        logging.info("Loading mempool from " + filePath)
        with open(filePath, 'r') as import_file:
            self.blockId = Path(filePath).stem
            for line in import_file:
                if 'txid' in line:
                    continue
                line = line.rstrip('\n')
                elements = line.split(SplitBy)
                txid = elements[0]
                # children are not stored in this file type
                tx = Transaction(txid, int(elements[1]), int(elements[2]), None, None, elements[3:])
                self.txs[txid] = tx
        import_file.close()
        logging.debug("Mempool loaded")
        logging.info(str(len(self.txs))+ " txs loaded")


    def backfill_relatives(self, confirmed_txs={}):
        startTime = time.time()
        for tx in self.txs.values():
            if tx.registered_with_ancestors:
                continue
            # Backfill ancestors
            allAncestors = set()
            searchList = list(set(tx.parents) | set(tx.ancestors))
            searched = set()
            while len(searchList) > 0:
                ancestor = searchList.pop()
                if (ancestor in searched):
                    continue
                else:
                    searched.add(ancestor)
                if (ancestor in self.txs):
                    allAncestors.add(ancestor)
                    searchList = list(set(searchList) | set(self.txs[ancestor].parents) | set(self.txs[ancestor].ancestors))
                elif (ancestor in confirmed_txs):
                    logging.debug(str(ancestor) + ' removed for being confirmed')
                else:
                    raise Exception(str(ancestor) + " not confirmed, and not in mempool")
            tx.ancestors = list(allAncestors)

            nonParentAncestors = set()
            for a in tx.ancestors:
                self.txs[a].descendants.add(tx.txid)
                nonParentAncestors.update(set(self.txs[a].ancestors).intersection(set(tx.ancestors)))
            tx.parents = set(tx.ancestors) - nonParentAncestors
            tx.permanent_parents = set(list(tx.parents))
            for p in tx.parents:
                self.txs[p].children.add(tx.txid)
            if len(tx.ancestors) < len(tx.parents):
                raise Exception("Fewer ancestors than parents")
            tx.registered_with_ancestors = True

        endTime = time.time()
        logging.info('Backfilling relatives finished, elapsed time: ' + str(endTime - startTime))


    def getTx(self, txid):
        return self.txs[txid]


    def getTxs(self):
        return self.txs


    def removeConfirmedTx(self, txid):
        for d in self.txs[txid].descendants:
            logging.debug("Remove confirmed tx: "  + txid + " from " + d)
            if d in self.txs.keys():
                if txid in self.txs[d].parents:
                    self.txs[d].parents.remove(txid)
                if txid in self.txs[d].ancestors:
                    self.txs[d].ancestors.remove(txid)

        for child in self.txs[txid].children:
            if child in self.txs.keys():
                if txid in self.txs[child].parents:
                    # Since every child is a descendant, this should never be true. If this is found, we need to fix descendant backfilling.
                    self.txs[child].parents.remove(txid)
                    logging.warning("Tx was in children, but not descendants")

        self.txs.pop(txid)


    def dropTx(self, txid):
        for a in self.txs[txid].ancestors:
            if a in self.txs.keys():
                if txid in self.txs[a].descendants:
                    self.txs[a].descendants.remove(txid)
                if txid in self.txs[a].children:
                    self.txs[a].children.remove(txid)

        for p in self.txs[txid].parents:
            if p in self.txs.keys():
                if txid in self.txs[p].children:
                    self.txs[p].children.remove(txid)
                    logging.warning("Tx was in parents, but not ancestors")

        self.txs.pop(txid)
