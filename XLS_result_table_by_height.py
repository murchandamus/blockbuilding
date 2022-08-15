import os
import logging
from xlwt import Workbook


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


def createBlockDictByHeight(dir, heights):
    blocks={}
    for height in heights:
        file = os.path.join(dir, [filename for filename in os.listdir(dir) if filename.startswith(str(height))][0])
        try:
            fee, weight = getBlockDetailsFromFile(file)
            type = file[file.rfind("."):]
        except TypeError:
            print("No such file by height: " + str(file)+ " "+str(height))
        blocks[height] = {"weight": weight, "fee": fee, "type": type}
    return blocks


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


if __name__ == '__main__':
    directory = input("dir?")
    OutputFile = input("output?")
    blockHeights, blockTypes = getBlockHeightsAndTypes(directory)
    BlockDict = createBlockDictByHeight(directory, blockHeights)
    writeBlockDetailsToXSLByHeight(OutputFile, BlockDict)
