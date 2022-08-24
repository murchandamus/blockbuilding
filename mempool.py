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


    def fromDict(self, txDict, backfill=True, confirmed_txs={}, blockId = 'dictionary'):
        self.blockId = blockId
        for txid, tx in txDict.items():
            self.txs[txid] = tx
        if backfill:
            self.backfill_relatives()


    def fromJSON(self, filePath, backfill=True, confirmed_txs={}):
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
        if backfill:
            self.backfill_relatives(confirmed_txs)


    def fromTXT(self, filePath, backfill=True, confirmed_txs={}, SplitBy=" "):
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
        if backfill:
            self.backfill_relatives(confirmed_txs)
        logging.debug("Mempool loaded")
        logging.info(str(len(self.txs))+ " txs loaded")


    # Recursive helper function for backfill_relatives() that ensures that
    # ancestors have been backfilled before adding them to a descendant
    def get_backfilled_ancestors(self, tx, backfilled, confirmed_txs={}):
        if tx.txid not in backfilled:
            # assume any ancestors may be parents
            all_ancestors = tx.parents.union(tx.ancestors)
            tx.parents = set(all_ancestors)
            tx.ancestors = set()
            for ancestor in all_ancestors:
                if ancestor in confirmed_txs:
                    logging.debug(str(ancestor) + ' removed for being confirmed')
                    tx.parents.remove(ancestor)
                    continue
                elif ancestor not in self.txs:
                    raise Exception(str(ancestor) + " not confirmed, and not in mempool")
                tx.ancestors.add(ancestor)
                further_ancestors = self.get_backfilled_ancestors(self.txs[ancestor], backfilled, confirmed_txs)
                # Prune ancestors of ancestors from parents
                tx.parents.difference_update(further_ancestors)
                tx.ancestors.update(further_ancestors)
            for a in tx.ancestors:
                self.txs[a].descendants.add(tx.txid)
            for p in tx.parents:
                self.txs[p].children.add(tx.txid)
            backfilled.add(tx.txid)
        return tx.ancestors


    def backfill_relatives(self, confirmed_txs={}):
        start_time = time.time()
        backfilled = set()
        for tx in self.txs.values():
            if tx.txid not in backfilled:
                # Recursively backfills parents before the called transaction itself
                self.get_backfilled_ancestors(tx, backfilled, confirmed_txs)
            # Transaction's parents and ancestors must be complete now
            tx.permanent_parents = set(list(tx.parents))

            if len(tx.ancestors) < len(tx.parents):
                raise Exception("Fewer ancestors than parents")

        end_time = time.time()
        logging.info('Backfilling relatives finished, elapsed time: ' + str(end_time - start_time))


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
