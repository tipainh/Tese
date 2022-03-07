# -*- coding: utf-8 -*-
"""
Created on Mon Feb 28 14:23:21 2022

@author: Tiago
"""

import math

def utility(FT,CT,NS):
    V=-0.0057*FT-0.0045*CT+2.5665*NS
    return V

def variations(n_elem,r_elem):
    var=math.factorial(n_elem)/math.factorial(n_elem-r_elem)
    return var

NA=4    # number of airports
A=list(range(1,NA+1))   # set of airports
FT_={(1,2):1, (1,3):2, (1,4):1, (2,1):1, (2,3):2, (2,4):1, (3,1):2, (3,2):2, (3,4):1, (4,1):1, (4,2):1, (4,3):1}    # set of flying times between O-D
Ti=10   # initial time
Tf=19   # final time
CT_max=3   # maximum waiting time or connecting time on ground

# Trip from origin airport to destination airport
O=1 #origin ariport
D=2 #destination airport
trip=[O,D]
NIday_0, NIday_1, NIday_2 = 0, 0, 0     # number of itineraries along the day
for flights in range(1,NA+1):
    stops=flights-1
    if flights==1:  # direct itineraries (0 stops)
        NI_0=variations(NA-2,stops)*CT_max**stops # number of itineraries (number of routes * different connecting times)
        print('There are',NI_0,'different direct itineraries')
        FT=FT_[(O,D)]   # flyting time
        CT=0    # connecting time
        NS=1    # binary variable defining if the flight is non-stop or not
        time=FT+CT  # time from O to D
        for t in range(Ti,Tf):
            if t+time<=Tf:
                NIday_0+=1
                V=utility(FT,CT,NS)
                print('Itinerary',O,'-',D,'starting at',t,'h and ending at',t+time,'h has V =',V)
        print('There are',NIday_0,'possible direct itineraries along the day')
    elif flights==2:    # one stop intineraries
        NI_1=variations(NA-2,stops)*CT_max**stops    # number of itineraries (number of routes * different connecting times)
        print('There are',NI_1,'different one stop itineraries')
        for j in [a for a in A if a not in trip]:   # running through airports that are not the origin nor the destination
            FT=FT_[(O,j)]+FT_[(j,D)]    # flying time
            for ct in range(1,CT_max+1):
                CT=ct   # connecting time
                NS=0    # binary variable defining if the flight is non-stop or not
                time=FT+CT  # time from O to D
                for t in range(Ti,Tf):
                    if t+time<=Tf:
                        NIday_1+=1
                        V=utility(FT,CT,NS)
                        print('Itinerary',O,'-',j,'-',D,'starting at',t,'h and ending at',t+time,'h has V =',V)
        print('There are',NIday_1,'possible one stop itineraries along the day')
    elif flights==3:    # two stops itineraries
        NI_2=variations(NA-2,stops)*CT_max**stops    # number of itineraries (number of routes * different connecting times)
        print('There are',NI_2,'different two stop itineraries')
        for j in [a for a in A if a not in trip]:   # running through airports that are not the origin nor the destination
            for k in [a for a in A if a not in trip]:   # running through airports that are not the origin nor the destination
                if j!=k:
                    FT=FT_[(O,j)]+FT_[(j,k)]+FT_[(k,D)] # flying time
                    for ct1 in range(1,CT_max+1):
                        for ct2 in range(1,CT_max+1):
                            CT=ct1+ct2  # connecting time
                            NS=0    # binary variable defining if the flight is non-stop or not
                            time=FT+CT  # time from O to D
                            for t in range(Ti,Tf):
                                if t+time<=Tf:
                                    NIday_2+=1
                                    V=utility(FT,CT,NS)
                                    print('Itinerary',O,'-',j,'-',k,'-',D,'starting at',t,'h and ending at',t+time,'h has V =',V)
        print('There are',NIday_2,'possible two stop itineraries along the day')

NI_OD=NI_0+NI_1+NI_2
print('There are',NI_OD,'different itineraries for the pair',O,'-',D,'airports')
NIday_OD=NIday_0+NIday_1+NIday_2
print('There are',NIday_OD,'possible itineraries along the day for the pair',O,'-',D,'airports')

NI_tot=NI_OD*variations(NA,2)
print('There are',NI_tot,'different itineraries for the entire network of',NA,'airports')
NIday_tot=NIday_OD*variations(NA,2)
print('There are',NIday_tot,'possible itineraries along the day for the entire network of',NA,'airports')