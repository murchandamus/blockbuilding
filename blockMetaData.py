from bs4 import BeautifulSoup
import urllib.request
import urllib.error
import ssl
import sys
import multiprocessing

def readUrl(blockId):
    url = "https://www.blockchain.com/btc/block/" + str(blockId)
    ssl._create_default_https_context = ssl._create_unverified_context  # specific for mac issues
    try:
        fp = urllib.request.urlopen(url)
        mybytes = fp.read()
        wsHtml = mybytes.decode("utf8")
        fp.close()
        soup = BeautifulSoup(wsHtml, 'html.parser')
    except urllib.error.HTTPError:
        print(str(blockId)+": Block not found ")
        pass
    except:
        print(str(blockId)+" Unexpected error:", sys.exc_info()[0])
        pass
    return soup


def getBlockDateTime(blockId):

    process = multiprocessing.Process(target=readUrl, args=(block,))
    process.join(10)
    if process.is_alive():
        print("no answer for "+ blockId)
        process.terminate()
        process.join()
    timestamp_string = readUrl(blockId).find("div", string="Timestamp").findNext('div').contents[0].contents[0]
    date, time = timestamp_string.split(' ')
    print(date)
    return date, time

def getBlockHeight(blockId):
    try:
        height_string = readUrl(blockId).find("div", string="Height").findNext('div').findNext('div').contents[0].contents[0]
    except:
        height_string='-1'
        pass
    return int(height_string)





if __name__ == '__main__':

    block = '00000000000000000010627e30472395f6b9a006f1784be048e40a48418ab8c7'

    print(getBlockDateTime(block))
#    print(getBlockHeight(block))
