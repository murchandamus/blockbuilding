import requests

def getBlockInfo(blockId):
    url = r"https://blockstream.info/api/block/" + str(blockId)
    blockdata = requests.get(url).json()
    # print(str(blockdata))
    print('height: ' + str(blockdata['height']))
    print('time: ' + str(blockdata['timestamp']))
    return blockdata

def getTxWeight(txid):
    url = r"https://blockstream.info/api/tx/" + str(txid)
    txdata = requests.get(url).json()
    # print(str(txdata))
    print('weight: ' + str(txdata['weight']))
    return txdata['weight']

if __name__ == '__main__':
    block = '00000000000000000010627e30472395f6b9a006f1784be048e40a48418ab8c7'
    tx = 'cae8f7930fef5704a8a55c19e5d52c3d7257ad5edec853e0729cd1db5d377a3b'
    getBlockInfo(block)
    getTxWeight(tx)
