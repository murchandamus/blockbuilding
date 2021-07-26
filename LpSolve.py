from ortools.linear_solver import pywraplp
import blockbuilder as bb


def LinearProgrammingSolve(txs, max_size, slover_choice='CBC', time_lim=5000):
    # Instantiate a solver, SAT is better by very very slow
    if slover_choice == 'CBC':
        solver = pywraplp.Solver('LinearProgrammingSolve',
                                 pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    elif slover_choice == 'SAT':
        solver = pywraplp.Solver('LinearProgrammingSolve',
                                 pywraplp.Solver.SAT_INTEGER_PROGRAMMING)
    solver.set_time_limit(time_lim)

    # Create variables
    lp_variables = {}
    for i in txs:
        lp_variables[i] = solver.IntVar(0, 1, i)

    # Size constraint:
    constraint0 = solver.Constraint(0, max_size)
    for i in txs:
        constraint0.SetCoefficient(lp_variables[i], txs[i].weight)


#   Ancestor constraints
    for i in txs:
        for j in txs[i].parents:
            solver.Add(lp_variables[j] >= lp_variables[i])
#            These might give different results in CBC:
#            solver.Add(lp_variables[i] <= lp_variables[j])
#            solver.Add(lp_variables[j] - lp_variables[i] >= 0)
#            solver.Add(0 <= lp_variables[j] - lp_variables[i])
#            solver.Add(lp_variables[i] - lp_variables[j] <= 0)


#     Objective function
    objective = solver.Objective()
    for i in txs:
        objective.SetCoefficient(lp_variables[i], txs[i].fee)
    objective.SetMaximization()

#     Solve the system.
    opt = " "
    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL:
        # not really optimal
        opt = 'optimal'
    else:
        opt = 'not optimal!'
    print(opt)

    opt_solution = sum(lp_variables[i].solution_value()*txs[i].fee for i in txs)

    print('Number of variables =', solver.NumVariables())
    print('Number of constraints =', solver.NumConstraints())
    # The value of each variable in the solution.
    print('Solution:')
    txs_to_include= {}
    for i in txs:
        if 0<lp_variables[i].solution_value()<1:
            print(lp_variables[i].solution_value())
        if lp_variables[i].solution_value() == 1:
            txs_to_include[i] = txs[i]
    # The objective value of the solution.
    print('Optimal objective value =', opt_solution)
    print("size = " + str(sum(lp_variables[i].solution_value()*txs[i].weight for i in txs)))
    print("value = " + str(sum(lp_variables[i].solution_value()*txs[i].fee for i in txs)))

    return sum(lp_variables[i].solution_value()*txs[i].fee for i in txs),\
        sum(lp_variables[i].solution_value()*txs[i].weight for i in txs), txs_to_include, opt


def create_block(txs_to_be_included):
#    print('all txs:', [i for i in txs_to_be_included])
    block = [i for i in txs_to_be_included if len(txs_to_be_included[i].parents) == 0]
    to_be_removed = []
    for k in block:
        txs_to_be_included.pop(k)
    while len(txs_to_be_included)>0:
        for i in txs_to_be_included:
            if len([j for j in txs_to_be_included[i].parents if j in block]) == len(txs_to_be_included[i].parents):
                block.append(i)
                to_be_removed.append(i)
        for i in to_be_removed:
            if i in txs_to_be_included:
                txs_to_be_included.pop(i)
    return block


def printToFile(txs, fee, weight, filePath, solver, optimal, blockId):
    if blockId is not None and blockId != "":
        filePath += blockId
    filePath += '.LpSolve'
    print('printing to: '+filePath)
    with open(filePath, 'w') as output_file:
        output_file.write('CreateNewBlockLpSolver(): fees ' + str(fee) + ' weight ' + str(
            weight) + ' solver ' + str(solver) + ' optimality ' + str(optimal) + '\n')
        print('printing LP solution ')
        for tx in txs:
            print('tx: '+str(tx))
            output_file.write(tx + '\n')
    output_file.close()


if __name__ == '__main__':
    mempool = bb.Mempool()
    mempool.fromTXT(r'./data/Dec17 sample/0000000000000000002d60720c6b9f5749ec01509844d05de1db08ca1ef06b52.mempool')
    solver = "CBC"
    timeLim = 1000000
    sizeLim = 4000000
    lp_fee, lp_weight, txs, isOpt = LinearProgrammingSolve(mempool.txs, sizeLim, solver, timeLim)
    block = create_block(txs)
    printToFile(block, lp_fee, lp_weight, 'test_LP/', solver, isOpt, mempool.blockId)

