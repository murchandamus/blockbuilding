import requests

def getBlockInfo(blockId):
    url = r"https://blockstream.info/api/block/" + str(blockId)
    response = requests.get(url)
    if (response.status_code == 404):
        print('Block not found: ' + blockId)
        return None
    else:
        return response.json()

def getTxWeight(txid):
    url = r"https://blockstream.info/api/tx/" + str(txid)
    response = requests.get(url)
    if (response.status_code == 404):
        print('Tx not found: ' + txid)
        return None
    else:
        txdata = requests.get(url).json()
        return txdata['weight']
