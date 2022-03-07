# -*- coding: utf-8 -*-
"""
Created on Sat Feb 12 12:02:49 2022

@author: Tiago
"""

from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('SCIP')
solver = pywraplp.Solver('SCIP', pywraplp.Solver.SCIP_MIXED_INTEGER_PROGRAMMING)

gap = 0.05
solverParams = pywraplp.MPSolverParameters()
solverParams.SetDoubleParam(solverParams.RELATIVE_MIP_GAP, gap)

#Constants
NF= 12	 # number of routes	
NR = 2  # number of aircraft types
NT = 10 # number of time periods
NA = 4 #number of airports
NWT = 3 #number of possible waiting times on the ground, for a connection

FL = list(range(1,NF+1))  # set of routes; 
T = list(range(1,NT+1)) # set of time periods;
R = list(range(1,NR+1))  # set of aircraft types;
A = list(range(1,NA+1)) #set of airports;
WT = list(range(1,NWT+1)) # set of waiting times;

#Parameters
z = [1,1] #number of aircraft of each type
s = [60,120] # seat capacity of aircraft type r
xmin = [1,0,1,1,1,0,0,1,0,1,0,0] # minimum number of flights in route f
smin = [60,0,120,50,100,0,0,100,0,120,0,0] # minimum number of seats in route f
ttf = [1,2,1,1,2,1,2,2,1,1,1,1] # travel time of route f
tta = [[0,1,2,1],[1,0,2,1],[2,2,0,1],[1,1,1,0]] # travel time of route departing a1 and arriving at a2
cF = [2000,3000] # cost of flying the airplane type r, per time period
cS = [[100,100],[100,100],[100,100],[100,100]] # cost of having an aircraft of type r on the ground for one time period, in airport a
q = [5,10,20,30,20,25,120,51,70,15,10,20] # demand in route f
l = [0.9,0.95,0.98,1,0.98,0.99,1,0.98,0.95,1,0.99,1] # maximum load factor in route f
cB=5 #time cost of being on board, for a passenger, per time period
cW=5 #time cost of being on the ground waiting, for a passenger, per time period
depF = [1,1,1,2,2,2,3,3,3,4,4,4] # number of the departure airport in route f
arrF = [2,3,4,1,3,4,1,2,4,1,2,3] #number of the arrival airport in route f

FF = {} # preprocessed variable, equal to one if flight in route f, departing at time t, arrives before the last time period
for f in FL:
    for t in T:
        if (t+ttf[f-1]<=NT):
            FF[(f,t)]=1
        else:
            FF[(f,t)]=0

d1 = {}  # preprocessed variable, equal to one if the one stop itinerary makes sense
for f in FL:
    for a in A:
        for t in T:
            for wt in WT:
                if arrF[f-1]!=NA and depF[f-1]!=a and arrF[f-1]!=a and t+ttf[f-1]+wt+tta[arrF[f-1]-1][a-1]<=NT:
                    d1[(f,a,t,wt)]=1
                elif arrF[f-1]==NA and wt!=0 and depF[f-1]!=a and arrF[f-1]!=a and t+ttf[f-1]+wt+tta[arrF[f-1]-1][a-1]<=NT:
                    d1[(f,a,t,wt)]=1
                else:
                    d1[(f,a,t,wt)]=0
                    
d2 = {} # preprocessed variable, equal to one if the  two stop itinerary makes sense
for f1 in FL:
    for f2 in FL:
        for t in T:
            for wt1 in WT:
                for wt2 in WT:
                    if arrF[f1-1]!=NA and depF[f2-1]!=NA and depF[f1-1]!=arrF[f2-1] and depF[f1-1]!=depF[f2-1] and arrF[f1-1]!=arrF[f2-1] and f1!=f2 and arrF[f1-1]!=depF[f2-1] and t+ttf[f1-1]+wt1+tta[arrF[f1-1]-1][depF[f2-1]-1]+wt2+ttf[f2-1]<=NT and wt1+wt2<=3:
                        d2[(f1,f2,t,wt1,wt2)]=1
                    elif arrF[f1-1]==NA and wt1!=0 and depF[f2-1]!=NA and depF[f1-1]!=depF[f2-1] and arrF[f1-1]!=arrF[f2-1] and f1!=f2 and arrF[f1-1]!=depF[f2-1] and t+ttf[f1-1]+wt1+tta[arrF[f1-1]-1][depF[f2-1]-1]+wt2+ttf[f2-1]<=NT and wt1+wt2<=3:
                        d2[(f1,f2,t,wt1,wt2)]=1
                    elif arrF[f1-1]!=NA and wt2!=0 and depF[f2-1]==NA and depF[f1-1]!=depF[f2-1] and arrF[f1-1]!=arrF[f2-1] and f1!=f2 and arrF[f1-1]!=depF[f2-1] and t+ttf[f1-1]+wt1+tta[arrF[f1-1]-1][depF[f2-1]-1]+wt2+ttf[f2-1]<=NT and wt1+wt2<=3:
                        d2[(f1,f2,t,wt1,wt2)]=1
                    else:
                        d2[(f1,f2,t,wt1,wt2)]=0

#Decision variables
x = {} #number of flights operating on route f, with aircraft type r departing at time t
y = {} #number of aircraft of type r on the ground, at airport a, at time t
uD = {} #number os passengers placed on direct routes, of route f
u1 = {} #number of passengers placed on one stop itineraries
u2 = {} #number of passengers placed on two stop itineraries
hd = {} #equal to 1 if at time t all the aircraft are departing the hub
gc = {} # will be greater than 1 if an aircraft if on the ground for more than 2h

for f in FL:
    for t in T:
        for r in R:
            x[(f,t,r)]=solver.IntVar(0,1,'x[%s,%s,%s]' %(f,t,r))
for a in A:
    for t in T:
        for r in R:
            y[(a,t,r)]=solver.IntVar(0,max(z),'y[%s,%s,%s]' %(a,t,r))
            gc[(a,t,r)]=solver.IntVar(0,1,'gc[%s,%s,%s]' %(a,t,r))
for f in FL:
    for t in T:
        uD[(f,t)]=solver.IntVar(0,max(s),'uD[%s,%s]' %(f,t))
for f in FL:
    for a in A:
        for t in T:
            for wt in WT:
                u1[(f,a,t,wt)]=solver.IntVar(0,max(s),'u1[%s,%s,%s,%s]' %(f,a,t,wt))
for f1 in FL:
    for f2 in FL:
        for t in T:
            for wt1 in WT:
                for wt2 in WT:
                    u2[(f1,f2,t,wt1,wt2)]=solver.IntVar(0,max(s),'u2[%s,%s,%s,%s,%s]' %(f1,f2,t,wt1,wt2))
for t in T:
    hd[(t)]=solver.IntVar(0,1,'hd[%s]' %(t))
     
#Objective function
objective_terms=[]

for f in FL:
    for t in T:
        for r in R:
            objective_terms.append(cF[r-1]*ttf[f-1]*x[(f,t,r)])
for a in A:
    for t in T:
        for r in R:
            objective_terms.append(cS[a-1][r-1]*gc[(a,t,r)])
for f in FL:
    for t in T:
        if FF[(f,t)]==1:
            objective_terms.append(cB*ttf[f-1]*uD[(f,t)])
for f in FL:
    for a in A:
        for t in T:
            for wt in WT:
                if d1[(f,a,t,wt)]==1:
                    objective_terms.append(cB*(ttf[f-1]+tta[arrF[f-1]-1][a-1])*u1[(f,a,t,wt)])
                    objective_terms.append(cW*(1+wt)*u1[(f,a,t,wt)])
for f1 in FL:
    for f2 in FL:
        for t in T:
            for wt1 in WT:
                for wt2 in WT:
                    if d2[(f1,f2,t,wt1,wt2)]==1:
                        objective_terms.append(cB*(ttf[f1-1]+tta[arrF[f1-1]-1][depF[f2-1]-1]+ttf[f2-1])*u2[(f1,f2,t,wt1,wt2)])
                        objective_terms.append(cW*(2+wt1+wt2)*u2[(f1,f2,t,wt1,wt2)])

solver.Minimize(solver.Sum(objective_terms))

#Constraints
#constraint 1: limits the use of aircraft to the available fleet
for t in T:
    for r in R:
        solver.Add(solver.Sum(y[(a,t,r)] for a in A) + solver.Sum(x[(f,t1,r)] for f in FL for t1 in T if t>=t1 and t<t1+ttf[f-1]) == z[r-1])

#constraint 2: continuity per node (a,t) and type r
for a in A:
    for t in T[1:]:
        for r in R:
            solver.Add(y[(a,t-1,r)] + solver.Sum(x[(f,t-ttf[f-1],r)] for f in FL if arrF[f-1]==a and t>ttf[f-1] and FF[(f,t-ttf[f-1])]==1) == y[(a,t,r)] + solver.Sum(x[(f,t,r)] for f in FL if depF[f-1]==a and FF[(f,t)]==1))

#constraint 3: the number of passengers carried is not greater than the available number of seats
for f in FL:
    for t in T:
        if FF[(f,t)]==1:
            solver.Add(solver.Sum(l[f-1]*s[r-1]*x[(f,t,r)] for r in R) >= uD[(f,t)] + solver.Sum(u1[(f,a,t,wt)] for a in A for wt in WT if d1[f,a,t,wt]==1) + solver.Sum(u1[(f1,a,t1,wt)] for f1 in FL for a in A for t1 in T for wt in WT if d1[f1,a,t1,wt]==1 and arrF[f1-1]==depF[f-1] and arrF[f-1]==a and t1+ttf[f1-1]+wt==t) + solver.Sum(u2[(f,f1,t,wt1,wt2)] for f1 in FL for wt1 in WT for wt2 in WT if d2[f,f1,t,wt1,wt2]==1) + solver.Sum(u2[(f1,f2,t1,wt1,wt2)] for f1 in FL for f2 in FL for t1 in T for wt1 in WT for wt2 in WT if d2[(f1,f2,t1,wt1,wt2)]==1 and arrF[f1-1]==depF[f-1] and depF[f2-1]==arrF[f-1] and t1+ttf[f1-1]+wt1==t) + solver.Sum(u2[f1,f,t1,wt1,wt2] for f1 in FL for t1 in T for wt1 in WT for wt2 in WT if d2[(f1,f,t1,wt1,wt2)]==1 and t1+ttf[f1-1]+wt1+tta[arrF[f1-1]-1][depF[f-1]-1]+wt2==t))

#constraint 4: the demand per market is satisfied
for f in FL:
    solver.Add(q[f-1] == solver.Sum(uD[(f,t)] for t in T if FF[(f,t)]==1) + solver.Sum(u1[(f1,a,t,wt)] for f1 in FL for a in A for t in T for wt in WT if depF[f-1]==depF[f1-1] and arrF[f-1]==a and d1[(f1,a,t,wt)]==1) + solver.Sum(u2[(f1,f2,t,wt1,wt2)] for f1 in FL for f2 in FL for t in T for wt1 in WT for wt2 in WT if depF[f-1]==depF[f1-1] and arrF[f2-1]==arrF[f-1] and d2[(f1,f2,t,wt1,wt2)]==1))

#constraint 5a: the number of flights between two airports is not smaller than an imposed (by the PSO standards) minimum
#constraint 5b: the number of seats between two airports is not smaller than an imposed (by the PSO standards) minimum
for f in FL:
    solver.Add(solver.Sum(x[(f,t,r)] for t in T for r in R if FF[(f,t)]==1) >= xmin[f-1])
    solver.Add(solver.Sum(s[r-1]*x[(f,t,r)] for t in T for r in R if FF[(f,t)]==1) >= smin[f-1])

#constraint 6: the number of aircrafts on the ground is an integer
# for a in A:
#     for t in T:
#         for r in R:
#             solver.Add(y[(a,t,r)] == int(y[(a,t,r)]))

# #constraint 7a: the number of aircrafts in the air is an integer
# for f in FL:
#     for t in T:
#         for r in R:
#             solver.Add(x[(f,t,r)] == 0 or 1)
# 		
# #constraint 8: number of passengers carried is an integer
# for f in FL:
#     for t in T:
#         if FF[(f,t)]==1:
#             solver.Add(uD[(f,t)] == int(uD[(f,t)]))
# 		
# #constraint 9: if the combination of flights and ground connections is possible, the number of passengers is an integer, for 1 stop itineraries
# for f in FL:
#     for a in A:
#         for t in T:
#             for wt in WT:
#                 solver.Add(u1[(f,a,t,wt)] == int(u1[(f,a,t,wt)]))

# #constraint 10: if the combination of flights and ground connections is possible, the number of passengers is an integer, for 2 stop itineraries
# for f1 in FL:
#     for f2 in FL:
#         for t in T:
#             for wt1 in WT:
#                 for wt2 in WT:
#                     solver.Add(u2[(f1,f2,t,wt1,wt2)] == int(u2[(f1,f2,t,wt1,wt2)]))

#constraint 11b: Aircrafts start the day at the hub
#constraint 11c:Aircrafts end the day at the hub
for r in R:
    solver.Add(solver.Sum(x[f,1,r] for f in FL if depF[f-1]==4) + y[(4,1,r)] == z[r-1])
    solver.Add(y[(NA,NT,r)] == z[r-1])
		
#constraint 12: there is only one aircraft operating each route at a certain moment in time
for t in T:
    for f in FL:
        solver.Add(solver.Sum(x[(f,t,r)] for r in R) <= 1)
			
#constraint 13: at any point in time, either no aircraft departs the hub, or all aircraft depart the hub
for t in T:
    solver.Add(solver.Sum(x[(f,t,r)] for f in FL for r in R if depF[f-1]==NA) == 2*hd[(t)])
		
#constraint 14: hd and gc are binary
# for t in T:
#     solver.Add(hd[(t)] == 0 or 1)
# for a in A:
#     for t in T:
#         for r in R:
#             solver.Add(gc[(a,t,r)] == 0 or 1)
		
#constraint 15: if an aircraft stays on the ground for more than 2h, a fee will be charged to the airline
for a in A:
    for t in T[:-3]:
        for r in R:
            solver.Add(gc[(a,t,r)] >= y[(a,t,r)] + y[(a,t+1,r)] + y[(a,t+2,r)] - 2.5)

# Solve
status = solver.Solve(solverParams)

if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
     print('Minimum cost = ', solver.Objective().Value(), '\n')
     print('Optimality gap = ', gap, '\n')
else:
    print('The problem does not have an optimal solution.')

#Post processing
p = {}
for f in FL:
    for t in T:
        for r in R:
            if x[(f,t,r)].solution_value() != 0:
                p[(f,t)] = uD[(f,t)] + solver.Sum(u1[(f,a,t,r)] for a in A for wt in WT) + solver.Sum(u1[(f1,a,t1,wt)] for f1 in FL for a in A for t1 in T for wt in WT if arrF[f1-1]==depF[f-1] and arrF[f-1]==a and t+ttf[f1-1]+wt==t) + solver.Sum(u2[(f,f1,t,wt1,wt2)] for f1 in FL for wt1 in WT for wt2 in WT) + solver.Sum(u2[(f1,f2,t1,wt1,wt2)] for f1 in FL for f2 in FL for t1 in T for wt1 in WT for wt2 in WT if arrF[f1-1]==depF[f-1] and depF[f2-1]==arrF[f-1] and t1+ttf[f1-1]+wt1==t) + solver.Sum(u2[(f1,f,t1,wt1,wt2)] for f1 in FL for t1 in T for wt1 in WT for wt2 in WT if t1+ttf[f1-1]+wt1+tta[arrF[f1-1]-1][depF[f-1]-1]+wt2==t)

with open('modelo_illustrative_Francisco_results.txt', 'w') as file, open('modelo_illustrative_Francisco_results_decision_variables.txt', 'w') as filee:
    file.write('The minimum cost is %s € \n' %solver.Objective().Value())
    
    for f in FL:
        for t in T:
            for r in R:
                if x[(f,t,r)].solution_value() >= 0.5:
                    file.write('There was one flight performed departing from %s at time %s arriving at %s at time %s, the type was %s carrying %s passengers aboard \n' %(depF[f-1], t, arrF[f-1], t+ttf[f-1], r, p[(f,t)].solution_value()))
                if x[(f,t,r)].solution_value() != 0:
                    filee.write('x [%s,%s,%s] = %s \n' %(f,t,r,x[(f,t,r)].solution_value()))
    for f in FL:
        for t in T:
            if uD[(f,t)].solution_value() >= 0.5:
                file.write('There were %s passengers transported, leaving from airport %s at time %s and arriving at airport %s at time %s \n' %(uD[(f,t)].solution_value(), depF[f-1], t, arrF[f-1], t+ttf[f-1]))
            if uD[(f,t)].solution_value() != 0:
                filee.write('uD [%s,%s] = %s \n' %(f,t,uD[(f,t)].solution_value()))
    for a in A:
        for t in T:
            for r in R:
                if y[(a,t,r)].solution_value() >= 0.5:
                    file.write('There were %s aircraft(s) on the ground at airport %s at time %s and the type was %s \n' %(y[(a,t,r)].solution_value(), a, t, r))
                if y[(a,t,r)].solution_value() != 0:
                    filee.write('y [%s,%s,%s] = %s \n' %(a,t,r,y[(a,t,r)].solution_value()))
    for f1 in FL:
        for a in A:
            for t in T:
                for wt in WT:
                    if u1[(f1,a,t,wt)].solution_value() >= 0.5:
                        file.write('There were %s passengers transported, leaving from airport %s at time %s with connection in airport %s arriving there at time %s and leaving at time %s to airport %s, landing at time %s \n' %(u1[(f1,a,t,wt)].solution_value(), depF[f1-1], t, arrF[f-1], t+ttf[f1-1], t+ttf[f1-1]+wt, a, t+ttf[f1-1]+wt+tta[arrF[f1-1]-1][a-1]))
                    if u1[(f1,a,t,wt)].solution_value() != 0:
                        filee.write('u1 [%s,%s,%s,%s] = %s \n' %(f1,a,t,wt,u1[(f1,a,t,wt)].solution_value()))
    for a in A:
        for t in T:
            for r in R:
                if gc[(a,t,r)].solution_value() == 1:
                    file.write('Aircraft type %s payed for ground costs at airport %s at time %s \n' %(r,a,t))
                if gc[(a,t,r)].solution_value() >= 0.5:
                    filee.write('gc [%s,%s,%s] = %s \n' %(a,t,r,gc[(a,t,r)].solution_value()))
    for f1 in FL:
        for f2 in FL:
            for t in T:
                for wt1 in WT:
                    for wt2 in WT:
                        if u2[(f1,f2,t,wt1,wt2)].solution_value() >= 0.5:
                            file.write('There were %s passengers transported, leaving from airport %s at time %s with connection in airports %s arriving at time %s and departing at time %s to connect at airport %s landing there at time %s and departing at time %s arriving at airport %s at time %s \n' %(u2[(f1,f2,t,wt1,wt2)].solution_value(), depF[f1-1], t, arrF[f1-1], t+ttf[f1-1], t+ttf[f1-1]+wt1, depF[f2-1], t+ttf[f1-1]+wt1+tta[arrF[f1-1]-1][depF[f2-1]-1], t+ttf[f1-1]+wt1+tta[arrF[f1-1]-1][depF[f2-1]-1]+wt2, arrF[f2-1], t+ttf[f1-1]+wt1+tta[arrF[f1-1]-1][depF[f2-1]-1]+wt2+ttf[f2-1]))
                        if u2[(f1,f2,t,wt1,wt2)].solution_value() != 0:
                            filee.write('u2 [%s,%s,%s,%s,%s] = %s \n' %(f1,f2,t,wt1,wt2,u2[(f1,f2,t,wt1,wt2)].solution_value()))
    for t in T:
        if hd[(t)].solution_value() != 0:
            filee.write('hd [%s] = %s \n' %(t,hd[(t)].solution_value()))