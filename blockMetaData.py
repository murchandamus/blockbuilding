from bs4 import BeautifulSoup
import urllib.request
import urllib.error
import ssl
import sys
import multiprocessing

def readUrl(Id, type):
    if type=='block':
        url = r"https://www.blockchain.com/btc/block/" + str(Id)
    elif type=='tx':
        url = r"https://www.blockchain.com/btc/tx/" + str(Id)
    ssl._create_default_https_context = ssl._create_unverified_context  # specific for mac issues
    try:
        fp = urllib.request.urlopen(url)
        mybytes = fp.read()
        wsHtml = mybytes.decode("utf8")
        fp.close()
        soup = BeautifulSoup(wsHtml, 'html.parser')
    except urllib.error.HTTPError:
        print(str(Id)+": Block not found ")
        pass
    except:
        print(str(Id)+" Unexpected error:", sys.exc_info()[0])
        pass
    return soup


def getBlockDateTime(blockId):

    timestamp_string = readUrl(blockId, 'block').find("div", string="Timestamp").findNext('div').contents[0].contents[0]
    date, time = timestamp_string.split(' ')
    print(date)
    return date, time

def getBlockHeight(blockId):
    try:
        height_string = readUrl(blockId, 'block').find("div", string="Height").findNext('div').findNext('div').contents[0].contents[0]
    except:
        height_string='-1'
        pass
    return int(height_string)



def getTxSize(txId):
    try:
        weightOfTx = readUrl(txId, 'tx').find("div", string='Size').findNext("div").findNext('div').contents[0].contents[0]
        if weightOfTx.find("bytes")!=-1:
            weightOfTx = weightOfTx[0:weightOfTx.find("bytes")-1]
        return weightOfTx
    except:
        print('tx not found '+ txId, sys.exc_info()[0])
        pass

if __name__ == '__main__':

    block = '00000000000000000010627e30472395f6b9a006f1784be048e40a48418ab8c7'
    tx = 'cae8f7930fef5704a8a55c19e5d52c3d7257ad5edec853e0729cd1db5d377a3b'
    print(getTxSize(tx))
    print(getBlockDateTime(block))
    print(getBlockHeight(block))
