%% This encoding does everything in one solving call benefiting from information generated beforehand such as the distances between answer sets.
%% Each cluster will pick an answer set with a single condition to meet.
%% 1) For two connected clusters, minimize the distance

#program base.

#show cluster/2.
%#show active_edge/4.
#show size/1.

%% For each answer set pick a node
1 { cluster(C,A) : answer_set(A) } 1 :- node(C).

%% No repeated answer sets in different clusters
:- cluster(C1,A), cluster(C2,A), C1!=C2.

%% Fix first solution
cluster(1,1).

#program edges(x,y).
edge(x,y).
%% Minimize the differences/distances between answer sets
#minimize{D,x,y : distance(A1,A2,D), cluster(x,A1), cluster(y,A2), edge(x,y), x<y }.


#program brave(x, y).
:- not cluster(x, y).
