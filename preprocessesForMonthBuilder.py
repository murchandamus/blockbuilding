import os
import blockMetaData as md


def addBlockHeightToFileName(fileLocation, fileName, height):
    if len(height) < 7:
        height = '0'*(7-len(height))+height
    os.rename(fileLocation+r'/'+fileName, fileLocation+ r'/' + height +'_' +fileName)


def addBlockHeightForDirectory(directory):
    relvantPathEndings = ['.mempool', '.block', '.gbt']
    for file in os.listdir(directory):
        if file.find("_") == -1 and any(x in file for x in relvantPathEndings):
            height = str(md.getBlockHeight(file[0:file.find(r'.')]))
            addBlockHeightToFileName(directory, file, height)

def createAllowListFile(directory, resultFile):
    print("start set")
    txSet = set()
    for file in os.listdir(directory):
        if file.endswith('.block'):
            print("looking at: "+file)
            with open(os.path.join(directory,file), 'r') as import_file:
                if file.find('_')!=-1:
                    height = file[0:7]
                else:
                    height = 'height not found'
                for line in import_file:
                    if 'txid' in line:
                        continue
                    line = line.rstrip('\n')#+' '+height
                    txSet.add(line)
            import_file.close()
    resFile = open(os.path.join(directory, resultFile+".allow"),'a')
    for tx in txSet:
        resFile.write(tx+'\n')
    resFile.close()
    return txSet

def getCoinbaseSizes(directory):
    coinbaseSizeDict = {}
    for file in os.listdir(directory):
        if file.endswith('.block'):
            blockNum = file[file.find('_')+1:file.find('.')]
            with open(os.path.join(directory, file), 'r') as import_file:
                import_file.readline()
                coinbaseTxId = import_file.readline()
                coinbaseSizeDict[blockNum] = md.getTxSize(coinbaseTxId)
    return coinbaseSizeDict


if __name__ == '__main__':
    directory = "/Users/clara/Documents/GitHub/blockbuilding/data/data_example/test"
    #addBlockHeightForDirectory(directory)
    createAllowListFile(directory, 'allow list')
    #print("dict "+str(getCoinbaseSizes(directory)))