%% This encoding does everything in one solving call benefiting from information generated beforehand such as the distances between answer sets.
%% Each cluster will pick an answer set with a single condition to meet.
%% 1) For two connected clusters, minimize the distance

%#const fix=0.

%% For each answer set pick a node
1 { cluster(C,A) : answer_set(A) } 1 :- node(C).

%% No repeated answer sets in different clusters
:- cluster(C1,A), cluster(C2,A), C1!=C2.

%% Maximize the differences/distances between answer sets
#minimize{D,X,Y : distance(A1,A2,D), cluster(X,A1), cluster(Y,A2), edge(X,Y), X<Y }.
%#maximize{D,X,Y : distance(A1,A2,D), cluster(X,A1), cluster(Y,A2), edge(X,Y), X<Y }.

%:- not cluster(1,1), fix=1.
cluster(1,1).

#show cluster/2.
%#show active_edge/4.
#show size/1.
