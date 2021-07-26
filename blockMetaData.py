from bs4 import BeautifulSoup
import urllib.request
import ssl



def getBlockDateTime(blockId):
    url = "https://www.blockchain.com/btc/block/" + str(blockId)

    fp = urllib.request.urlopen(url)
    mybytes = fp.read()
    wsHtml = mybytes.decode("utf8")
    fp.close()

    soup = BeautifulSoup(wsHtml, 'html.parser')

    timestamp_string = soup.find("div", string="Timestamp").findNext('div').contents[0].contents[0]

    date, time = timestamp_string.split(' ')
    return date, time

def getBlockHeight(blockId):
    url = "https://www.blockchain.com/btc/block/" + str(blockId)

    fp = urllib.request.urlopen(url)
    mybytes = fp.read()
    wsHtml = mybytes.decode("utf8")
    fp.close()

    soup = BeautifulSoup(wsHtml, 'html.parser')
    height_string = soup.find("div", string="Height").findNext('div').findNext('div').contents[0].contents[0]
    return int(height_string)

if __name__ == '__main__':
    ssl._create_default_https_context = ssl._create_unverified_context #specific for mac issues
    block = '00000000000000000010627e30472395f6b9a006f1784be048e40a48418ab8c7'
    print(getBlockDateTime(block))
    print(getBlockHeight(block))
