import os
import blockMetaData as md

def addBlockHeightToFileName(fileLocation, fileName, height):
    if len(height) < 6:
        height = '0'*(6-len(height))+height
    os.rename(fileLocation+r'/'+fileName, fileLocation+ r'/' + height +'_' +fileName)

def addBlockHeightForDirectory(directory):
    relevant_path_endings = ['.mempool', '.block', '.gbt']
    blockHeights = {}
    for file in os.listdir(directory):
        if file.find("_") == -1 and any(x in file for x in relevant_path_endings):
            blockId = file[0:file.find(r'.')]
            height = -1
            if blockId in blockHeights:
                height = int(blockHeights[blockId])
            else:
                blockData = md.getBlockInfo(blockId)
                if (blockData != None):
                    height = int(blockData['height'])
                    blockHeights[blockId] = height
                elif (blockData == None):
                    os.rename(file, 'X_' + file + '_not_found')
                    print("height for " + blockId + " not found")
                    continue
            if height < 0:
                raise Exception("height for " + blockId + " not found")
            addBlockHeightToFileName(directory, file, str(height))

def createAllowListFile(directory, resultFile):
    print("start allowset")
    txSet = set()
    for file in os.listdir(directory):
        if file.endswith('.block'):
            print("looking at: "+file)
            with open(os.path.join(directory,file), 'r') as import_file:
                if file.find('_')!=-1:
                    height = file[0:6]
                else:
                    height = 'height not found'
                for line in import_file:
                    # Skip header line in block file
                    if 'fees' in line:
                        continue
                    line = line.rstrip('\n')#+' '+height
                    txSet.add(line)
            import_file.close()
    resFile = open(os.path.join(directory, resultFile+".allow"),'a')
    for tx in txSet:
        resFile.write(tx+'\n')
    resFile.close()
    return txSet

def createCoinbaseWeightsDict(directory, resultFile):
    coinbaseWeights = {}
    coinbase_file_name = os.path.join(directory, resultFile+'.coinbases')
    if (os.path.exists(coinbase_file_name)):
        with open(coinbase_file_name, 'w') as from_file:
             for line in from_file:
                 lineItems = line.rstrip('\n').split(' ')
                 coinbaseWeights[int(lineItems[0])] = lineItems[1]
    resFile = open(coinbase_file_name,'w')

    for file in os.listdir(directory):
        if file.endswith('.block'):
            print("Looking for coinbase weight for " + file)
            height = file[0:file.find('_')]
            if coinbaseWeights.has(height):
                continue
            else:
                with open(os.path.join(directory, file), 'r') as import_file:
                    import_file.readline()
                    coinbaseTxId = import_file.readline().rstrip('\n')
                    coinbaseWeights[height] = md.getTxWeight(coinbaseTxId)
                    resFile.write(str(height + ' ' + str(weight) + '\n')
    resFile.close()

if __name__ == '__main__':
    directory = '.'
    addBlockHeightForDirectory(directory)
    createAllowListFile(directory, 'txset')
    createCoinbaseWeightsDict(directory, 'weight')
    #print("dict "+str(getCoinbaseSizes(directory)))
