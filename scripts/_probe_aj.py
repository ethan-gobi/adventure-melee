import sys, collections
sys.path.insert(0, r'C:\adventure-melee\scripts')
from hsd import *
from HSDRaw.Tools.Melee import FighterAJManager
import System
from System.Reflection import BindingFlags
t = clr.GetClrType(FighterAJManager)
for m in t.GetMethods(BindingFlags.Public|BindingFlags.Instance|BindingFlags.Static|BindingFlags.DeclaredOnly): print('AJ', m)
for c in t.GetConstructors(): print('AJ ctor', c)
