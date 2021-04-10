import LpSolve as lp
import blockbuilder as bb
import os
from xlwt import Workbook



if __name__ == '__main__':
    file_dir = input("dir? ") or r"data/data_example"
#    mempool.fromTXT(r'./data/Dec17 sample/0000000000000000002d60720c6b9f5749ec01509844d05de1db08ca1ef06b52.mempool')
    timeLim = int(input("time lim? ") or 10000)
    max_size = int(input("block size lim? ") or 4000000)
    Solver = input("which solver? (CBC/SAT) ") or "CBC"
    ResFile = input("result file? ") or "testResults"
    LimitOnNumberOfBlocks = int(input("Lin num of blocks? 0 for no ") or 0)
    workBookName = ResFile+'.xls'

    j = 0
    wb = Workbook()
    sheet1 = wb.add_sheet('Sheet 1')
    sheet1.write(j, 0, "block_num")
    sheet1.write(j, 1, "timestamp")
    sheet1.write(j, 2, "LP_fee")
    sheet1.write(j, 3, "LP_size")
    sheet1.write(j, 4, "past_fee")
    sheet1.write(j, 5, "past_size")
    sheet1.write(j, 6, "bitcoin_core_fee")
    sheet1.write(j, 7, "bitcoin_core_size")
    j = j + 1
    for filename in os.listdir(file_dir):
        if filename.endswith(".mempool"):
            print("Block number: " + str(j))
            block_num = filename[:-8]
            print("Block: " + str(block_num))
            mempool = bb.Mempool()
            mempool.fromTXT(os.path.join(file_dir, block_num+".mempool"))
            LP_fee, LP_size, New_Block_txs, opt = lp.LinearProgrammingSolve(mempool.txs, max_size, Solver, timeLim)
            New_Block = lp.create_block(New_Block_txs)
            #past_fee, past_size = find_past_fee_and_size(file_dir)
            #chain_code_fee, chain_code_size = find_past_fee_and_size(file_dir, ".gbt")
            #if FindBlockTime == 1:
            #    time_stamp = find_block_time(block_num)
            #else:
            time_stamp = 0
            sheet1.write(j, 0, block_num)
            sheet1.write(j, 1, time_stamp)
            sheet1.write(j, 2, LP_fee)
            sheet1.write(j, 3, LP_size)
            sheet1.write(j, 4, "-")
            sheet1.write(j, 5, "-")
            sheet1.write(j, 6, "-")
            sheet1.write(j, 7, "-")
            sheet1.write(j, 8, opt)

            block_file = open(os.path.join(file_dir, str(block_num) + ".LpBlock"), 'w')
            for line in New_Block:
                block_file.write(line + '\n')
            block_file.close()
            wb.save(os.path.join(file_dir, workBookName))
            j = j + 1

            if LimitOnNumberOfBlocks != 0 and j > LimitOnNumberOfBlocks:
                break
    wb.save(workBookName)

