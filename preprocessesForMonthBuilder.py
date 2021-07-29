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




if __name__ == '__main__':
    directory = input("dir? ")
    addBlockHeightForDirectory(directory)
