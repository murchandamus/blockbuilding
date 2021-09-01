import os

def renameByClusterFiles(directory, referenceDir):
    currentDir = os.path.split(os.getcwd())[-1]
    if currentDir != 'results':
        raise Exception("Script should be executed in '/results' folder")
    suffix = '.byclusters'
    for fileName in os.listdir(directory):
        blockHeight = fileName[0:6]
        for file in os.listdir(referenceDir):
            if file.startswith(blockHeight):
                blockId = file[0:file.find(r'.')]
                os.rename(directory+r'/'+fileName, directory+ r'/' + blockId + suffix)
                break;

if __name__ == '__main__':
    # directory = '/home/murch/blockbuilding/May2020-by-month-extended-allow/results'
    # parentDir = '/home/murch/blockbuilding/May2020-by-month'
    directory = '.'
    parentDir = './..'
    renameByClusterFiles(directory, parentDir)
