import pandas as pd
import os
import csv

class Summary():
    def __init__(self, sim_id, keys=['total fees', 'average fee', 'median fee', 'var of fee']):
        self.id = sim_id
        self.blockInSim = -1
        self.blocksByCluster = -1
        self.keys = keys
        self.resCluster = dict.fromkeys(self.keys, -1)
        self.resAncestor = dict.fromkeys(self.keys, -1)
        self.resDiff = dict.fromkeys(self.keys, -1)


def find_stats(res, baseline, sim_id):
    sum = Summary(sim_id)
    sum.blockInSim = res.shape[0]
    joinedRes = res.join(baseline, lsuffix='_res', rsuffix='_baseline')
    print('res:')
    print(res['fee'])
    print('joined table, fee_res')
    print(joinedRes['fee_res'])
    f_data = joinedRes[joinedRes['type_res'] =='.byclusters']
    sum.blocksByCluster = f_data.shape[0]
    print(f_data['fee_baseline'])
    sum.resCluster['total fees'] = f_data['fee_res'].sum()
    sum.resCluster['average fee'] = f_data['fee_res'].mean()
    sum.resCluster['median fee'] = f_data['fee_res'].median()
    sum.resCluster['var of fee'] = f_data['fee_res'].var()
    sum.resAncestor['total fees'] = f_data['fee_baseline'].sum()
    sum.resAncestor['average fee'] = f_data['fee_baseline'].mean()
    sum.resAncestor['median fee'] = f_data['fee_baseline'].median()
    sum.resAncestor['var of fee'] = f_data['fee_baseline'].var()
    for key in sum.resCluster.keys():
        sum.resDiff[key] = sum.resCluster[key] - sum.resAncestor[key]
    return sum


def find_res_file_in_folder(folder):
    for file in os.listdir(folder):
        if file.endswith('.csv'):
            return os.path.join(folder, file)


def summ_exp(folder, baselineDir):
    exp_dict = {}
    baseline_data = pd.read_csv(find_res_file_in_folder(baselineDir))
    for exp_folder in os.listdir(folder):
        d = os.path.join(folder,exp_folder)
        if os.path.isdir(d):
            res = pd.read_csv(find_res_file_in_folder(d))
            exp_dict[exp_folder] = find_stats(res, baseline_data, exp_folder)
    return exp_dict


def sum_month(month_folder):
    baseline_folder = os.path.join(month_folder, 'baseline')
    for subfolder in os.listdir(month_folder):
        if os.path.isdir(os.path.join(month_folder, subfolder)) and ('baseline' not in subfolder):
            exp_summery = summ_exp(os.path.join(month_folder, subfolder), baseline_folder)
            print_to_file(os.path.join(month_folder, 'res_'+str(subfolder)+'.csv'), exp_summery)


def print_to_file(file_path, dict):
    with open(file_path, 'w', newline='') as csv_file:
        header = ['id','blocks in sim', 'blocks by Cluster'] + [x+'_byCluster' for x in keys] + [x+'_byAncestor' for x in keys] + [x+'_diff' for x in keys]
        writer = csv.writer(csv_file)
        writer.writerow(header)
        for res in dict.keys():
            row = [dict[res].id, dict[res].blockInSim, dict[res].blocksByCluster]+list(dict[res].resCluster.values())+list(dict[res].resAncestor.values())+list(dict[res].resDiff.values())
            writer.writerow(row)
    csv_file.close()


if __name__ == '__main__':
    keys = ['total fees', 'average fee', 'median fee', 'var of fee']
    sum_month('complete-results')
