import heapq
import json
import math
from pathlib import Path
import logging

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
        # backfill children from parents
        self.backfill_relatives()

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
        import_file.close()
        # backfill children from parents
        self.backfill_relatives()

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
        # backfill children from parents
        self.backfill_relatives()
        logging.info(str(len(self.txs))+ " txs loaded")

    def backfill_relatives(self):
        logging.debug("Backfill, ancestors, parents and children from parents and ancestors...")
        for tx in self.txs.values():
            # Backfill ancestors
            allAncestors = set()
            searchList = list(set(tx.immutable_parents) | set(tx.unconfirmed_ancestors))
            while len(searchList) > 0:
                ancestor = searchList.pop()
                allAncestors.add(ancestor)
                furtherAncestors = set(self.txs[ancestor].immutable_parents) | set(self.txs[ancestor].unconfirmed_ancestors)
                searchList = list(set(searchList) | furtherAncestors)
            tx.unconfirmed_ancestors = list(set(allAncestors))

            nonParentAncestors = set()
            for a in tx.unconfirmed_ancestors:
                self.txs[a].descendants.add(tx.txid)
                nonParentAncestors.update(set(self.txs[a].unconfirmed_ancestors).intersection(set(tx.unconfirmed_ancestors)))
            tx.immutable_parents = set(tx.unconfirmed_ancestors) - nonParentAncestors
            for p in tx.immutable_parents:
                self.txs[p].children.add(tx.txid)
            if len(tx.unconfirmed_ancestors) < len(tx.immutable_parents):
                raise Exception("Fewer ancestors than parents")

        logging.debug("Ancestors, parents, and children backfilled")

    def getTx(self, txid):
        return self.txs[txid]

    def getTxs(self):
        return self.txs

    def removeConfirmedTx(self, txid):
        for d in self.txs[txid].descendants:
            print("Remove confirmed tx: "  + txid + " from " + d)
            if d in self.txs.keys():
                if txid in self.txs[d].unconfirmed_ancestors:
                    self.txs[d].unconfirmed_ancestors.remove(txid)

        for child in self.txs[txid].children:
            if child in self.txs.keys():
                if txid in self.txs[child].unconfirmed_ancestors:
                    self.txs[d].unconfirmed_ancestors.remove(txid)
                    # Since every child is a descendant, this should never be true. If this is found, we need to fix descendant backfilling.
                    raise Exception("Tx was in children, but not descendants")

        self.txs.pop(txid)

    def dropTx(self, txid):
        for a in self.txs[txid].unconfirmed_ancestors:
            if a in self.txs.keys():
                if txid in self.txs[a].descendants:
                    self.txs[a].descendants.remove(txid)
                if txid in self.txs[a].children:
                    self.txs[a].children.remove(txid)

        for p in self.txs[txid].immutable_parents:
            if p in self.txs.keys():
                if txid in self.txs[p].children:
                    self.txs[p].children.remove(txid)
                    logging.warning("Tx was in parents, but not ancestors")

        self.txs.pop(txid)
