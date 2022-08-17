import argparse
import csv
import os
import logging
import sys

def main(argv):
    parser = argparse.ArgumentParser(description='Builds a .csv table from the results of month_builder')
    parser.add_argument('-s', '--source', default='.', help='directory with the block files, uses current directory if not specified')
    parser.add_argument('-o', '--output', default='./fee_weight_per_block.csv', help='output file the resulting table will be written into')

    args = parser.parse_args()
    block_heights, block_types = getBlockHeightsAndTypes(args.source)
    block_dict = createBlockDictByHeight(args.source, block_heights)
    write_blocks_to_csv(args.output, block_dict)

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
    block_types = list(set(fileTypes) & set(allowedBlockTypes))
    blockIdSet = set()
    for f in files:
        if f.endswith(tuple(block_types)):
            blockIdSet.add(f[:f.find('-')])
    block_heights = list(blockIdSet)
    return block_heights, block_types


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


def write_blocks_to_csv(csv_file_name, blocks):
    print("Printing by height")
    with open(csv_file_name, 'w', newline='') as csv_file:
        fieldnames = ['height', 'weight', 'fee', 'type']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for height in blocks.keys():
            writer.writerow({'height': height, 'weight': blocks[height]['weight'], 'fee': blocks[height]['fee'], 'type': blocks[height]['type']})

    csv_file.close()

if __name__ == '__main__':
    main(sys.argv[1:])
