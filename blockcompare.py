import os
from xlwt import Workbook

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

def getBlockNumbersAndTypes(directory = r"./blockCompareTest"):
    files = os.listdir(directory)
    blockNumbers = list(dict.fromkeys([f[:f.find(".")] for f in files]))
    blockTypes = list(dict.fromkeys([f[f.find("."):] for f in files]))
    blockNumbers.remove("")
    blockTypes.remove('.DS_Store')
    return blockNumbers, blockTypes


def createBlockDic(blockNumbers, filetypes):
    blocks={}
    for block in blockNumbers[:]:
        weights = {}
        fees = {}
        for inp in filetypes:
            blockFileName = block + inp
            try:
                fees[inp], weights[inp] = getBlockDetailsFromFile(os.path.join(directory, blockFileName))
            except TypeError:
                print("No such file: "+str(os.path.join(directory, block + inp)))
            blocks[block] = Block(str(block), weights, fees)
    return blocks

def writeBlockDetailsToXSL(xlsFileName, blockDetails, blockTypes):
    wb = Workbook()
    sheet1 = wb.add_sheet('Results', cell_overwrite_ok=True)
    inputs = blockDetails[next(iter(blockDetails))].weights.keys()
    line = 0
    k = 1
    sheet1.write(line , 0, 'Block ID')
    for inp in blockTypes:
        print('input type: ' + str(inp))
        sheet1.write(line, k, str(inp) + ' weight')
        sheet1.write(line, k+1, str(inp) + ' fees')
        k += 2
    line +=1
    for blockNum in blockDetails.keys():
        sheet1.write(line, 0, blockNum)
        k=1
        print('writing Block '+ str(blockNum))
        for inp in blockTypes:
            sheet1.write(line, k, blockDetails[blockNum].weights[inp])
            print('line: '+ str(line)+' k: ' + str(k)+  ' write weight '+ str(blockDetails[blockNum].weights[inp]))
            sheet1.write(line,k+1,blockDetails[blockNum].totalFees[inp])
            print('line: '+ str(line)+' k: ' + str(k)+  ' write fee '+ str(blockDetails[blockNum].totalFees[inp]))
            k += 2
        print('moving to next block')
        line += 1
    wb.save(xlsFileName)

if __name__ == '__main__':
    directory = r"./blockCompareTest"
    blockNum, blockTypes = getBlockNumbersAndTypes()
    print(blockTypes)
    BlockDic = createBlockDic(blockNum, blockTypes)
    for block in BlockDic:
        print(BlockDic[block].blockNumber)
        print(BlockDic[block].weights)
        print(BlockDic[block].totalFees)
    writeBlockDetailsToXSL("checkXSL123.xls", BlockDic, blockTypes)
