import sys; sys.path.insert(0,'scripts')
from sonic_anim_lib import *
S=P()
tests=[("stand",S),("pitch30",P(S,root=(30,0,0))),("kickR",P(S,thighR=(0,-0.2,1),shinR=(0,-0.2,1))),("armLfwd",P(S,armL=(0,0,1),foreL=(0,0,1))),
       ("yawL45",P(S,root=(0,45,0))),("chestyaw",P(S,chest=(0,45,0))),("headdown",P(S,head=(30,0,0)))]
an=Anim("Wait1",len(tests)-1,[(i,p,"lin") for i,(n,p) in enumerate(tests)])
sheet([("t",an,list(range(len(tests))))],"work/v19/t_pose.png")
