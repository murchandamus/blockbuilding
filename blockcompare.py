import blockbuilder
import os

class Block():
    def __init__(self, blockNumer, weightsDic, totalFeeDic):
        self.blockNumber = blockNumer
        self.weights = weightsDic
        self.totalFees = totalFeeDic

def getBlockDetailsFromFile(fileLocation):
    try:
        blockDetails = open(fileLocation, 'r')
        firstline = blockDetails.readline()
        totalFee = firstline[firstline.find("fees") + 5:firstline.find("weight") - 1]
        weight = firstline[firstline.find("weight") + 7:]
        blockDetails.close()
        return totalFee, weight
    except FileNotFoundError:
        print("No such file")

def createBlockDic(directory = r"./blockCompareTest" ):
    blocks = {}
    files = os.listdir(directory)
    blockNumbers = list(dict.fromkeys([f[:f.find(".")] for f in files]))
    blockNumbers.remove("")
    for block in blockNumbers[:]:
        weights = {}
        fees = {}
        fees["gbt"], weights["gbt"] = getBlockDetailsFromFile(os.path.join(directory, block + ".gbt"))
        fees["txt"], weights["txt"] = getBlockDetailsFromFile(os.path.join(directory, block + ".txt"))
        blocks[block] = Block(str(block), weights, fees)
    return blocks


if __name__ == '__main__':
    directory = r"./blockCompareTest"
    b = createBlockDic()
    for block in b:
        print(b[block].blockNumber)
        print(b[block].totalFees)