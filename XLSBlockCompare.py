import os
from xlwt import Workbook

class Block():
    def __init__(self, blockNumber, weightsDic, totalFeeDic):
        self.blockNumber = blockNumber
        self.weights = weightsDic
        self.totalFees = totalFeeDic


def getBlockDetailsFromFile(fileLocation):
    try:
        blockDetails = open(fileLocation, 'r')
        firstline = blockDetails.readline().strip()
        lineItems = firstline.split(" ")
        totalFee = lineItems[lineItems.index("fees") + 1]
        weight = lineItems[lineItems.index("weight") + 1]
        blockDetails.close()
        return totalFee, weight
    except FileNotFoundError:
        print("No such file to get from "+str(fileLocation))
    except:
        print("some thing else is wrong with " + str(fileLocation))


def getBlockNumbersAndTypes(directory = r"./blockCompareTest"):
    files = os.listdir(directory)
    fileTypes = list(dict.fromkeys([f[f.rfind("."):] for f in files]))
    print('file types:')
    print(fileTypes)
    allowedBlockTypes = ['.gbt', '.block', '.byclusters', '.LpSolve', '.byancestors']
    blockTypes = list(set(fileTypes) & set(allowedBlockTypes))
    blockIdSet = set()
    for f in files:
        if f.endswith(tuple(blockTypes)):
            blockIdSet.add(f[:f.find('.')])
    blockNumbers = list(blockIdSet)
    return blockNumbers, blockTypes


def getBlockHeightsAndTypes(directory):
    files = os.listdir(directory)
    fileTypes = list(dict.fromkeys([f[f.rfind("."):] for f in files]))
    print('file types:')
    print(fileTypes)
    allowedBlockTypes = ['.gbt', '.block', '.byclusters', '.LpSolve', '.byancestors']
    blockTypes = list(set(fileTypes) & set(allowedBlockTypes))
    blockIdSet = set()
    for f in files:
        if f.endswith(tuple(blockTypes)):
            blockIdSet.add(f[:f.find('-')])
    blockHeights = list(blockIdSet)
    return blockHeights, blockTypes

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


def createBlockDicByHeight(dir, heights):
    blocks={}
    for height in heights:
        file = os.path.join(dir, [filename for filename in os.listdir(dir) if filename.startswith(str(height))][0])
        try:
            fee, weight = getBlockDetailsFromFile(file)
            type = file[file.rfind("."):]
        except TypeError:
            print("No such file by height: " + str(file)+ " "+str(height))
        blocks[height] = {"weight": weight, "fee": fee, "type": type}
        print('weight ' + str(weight))
    return blocks


def writeBlockDetailsToXSL(xlsFileName, blockDetails, blockTypes):
    print("file name is "+str(xlsFileName))
    print("BlockDic: "+str(blockDetails))
    print("Types: "+str(blockTypes))
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
            try:
                sheet1.write(line, k, blockDetails[blockNum].weights[inp])
                print('line: '+ str(line)+' k: ' + str(k)+  ' write weight '+ str(blockDetails[blockNum].weights[inp]))
                sheet1.write(line,k+1,blockDetails[blockNum].totalFees[inp])
                print('line: '+ str(line)+' k: ' + str(k)+  ' write fee '+ str(blockDetails[blockNum].totalFees[inp]))
            except KeyError:
                print('key error, inp:'+ str(inp) + 'blockNum: '+str(blockNum))
                sheet1.write(line, k, 'key error'+str(inp))
                sheet1.write(line, k+1, 'key error' + str(inp))

            k += 2
        print('moving to next block')
        line += 1
    wb.save(xlsFileName)



def writeBlockDetailsToXSLByHeight(xlsFileName, blocks):
    print("printing by Height")
    wb = Workbook()
    sheet1 = wb.add_sheet('Results', cell_overwrite_ok=True)
    sheet1.write(0, 0, "height")
    sheet1.write(0, 1, "weight")
    sheet1.write(0, 2, "fee")
    sheet1.write(0, 3, "type")
    line = 1
    for height in blocks.keys():
        sheet1.write(line,0,height)
        sheet1.write(line, 1, blocks[height]["weight"])
        sheet1.write(line, 2, blocks[height]["fee"])
        sheet1.write(line, 3, blocks[height]["type"])
        line += 1
    wb.save(xlsFileName)


    return 0



if __name__ == '__main__':
#    directory = input("which directory? ")
#    OutputFile = input("where to send results? ")
    directory = input("dir?")
    OutputFile = input("output?")
#    blockNum, blockTypes = getBlockNumbersAndTypes(directory)
    blockHeights, blockTypes = getBlockHeightsAndTypes(directory)
    print(blockHeights)
#    BlockDic = createBlockDic(blockHeights, blockTypes)
    BlockDic = createBlockDicByHeight(directory, blockHeights)
    for block in BlockDic:
        print(BlockDic[block])
    writeBlockDetailsToXSLByHeight(OutputFile, BlockDic)
#    writeBlockDetailsToXSL(OutputFile, BlockDic, blockTypes)
