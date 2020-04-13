from igraph import *
import igraph
import numpy as np

def sim(n, edges, pout=0.01, pedge=0.1, nstep=10, ntrial=10000):
    statesum = np.zeros(n)
    for it in range(0, ntrial):
        state = np.zeros(n)
        for k in range(0, nstep):
            # internal infektions
            statenew = state.copy()
            for x in edges:
                if state[x[0]] != state[x[1]]:
                    if np.random.random() < pedge:
                        statenew[x[0]] = 1
                        statenew[x[1]] = 1
            rans = np.random.random(size=n)
            state = np.where(rans < pout, 1, statenew)
        statesum = statesum + state
    return statesum/ntrial

childs = 4
levels = 2
n = sum([childs**i for i in range(0, levels)])
g = Graph.Tree(n, childs)
edges = g.get_edgelist()
sim(n,edges, ntrial=1000000, pout=0.0005, pedge=0.1, nstep=10)
