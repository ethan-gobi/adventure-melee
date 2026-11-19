import sys
sys.path.insert(0, r'C:\adventure-melee\scripts')
from hsd import *
import System
from System.Reflection import BindingFlags
asm=[a for a in System.AppDomain.CurrentDomain.GetAssemblies() if a.GetName().Name=='HSDRaw'][0]
bf = BindingFlags.Public|BindingFlags.Instance|BindingFlags.Static|BindingFlags.DeclaredOnly
def show(n, fields=True):
    t=asm.GetType(n); print('==',n)
    for c in t.GetConstructors(): print('  ctor',c)
    for m in t.GetMethods(bf):
        if not m.Name.startswith(('get_','set_')): print('  ', 'static' if m.IsStatic else '', m)
    for p in t.GetProperties(bf): print('  prop',p.PropertyType.Name,p.Name)
    if fields:
        for fl in t.GetFields(bf): print('  field',fl.FieldType.Name,fl.Name)
for n in ['HSDRaw.Tools.POBJ_Generator','HSDRaw.GX.GX_Vertex','HSDRaw.Tools.GXImageConverter','HSDRaw.Common.HSD_MOBJ','HSDRaw.Common.HSD_Material','HSDRaw.Common.HSD_DOBJ']:
    show(n)
t=asm.GetType('HSDRaw.Common.HSD_TOBJ'); print('== TOBJ methods'); 
for m in t.GetMethods(bf):
    if not m.Name.startswith(('get_','set_')): print('  ',m)
for n in asm.GetTypes():
    if n.IsPublic and ('TOBJ' in n.Name or 'Texture' in n.Name) and n.FullName!='HSDRaw.Common.HSD_TOBJ': print('type',n.FullName)
# existing rigid dobj on bone 5
f = HSDRawFile(r'C:\adventure-melee\work\v04\PlSnNr.dat')
root=[r for r in f.Roots if r.Data.GetType().Name=='HSD_JOBJ'][0].Data
js=jobj_list(root)
for bi in (5, 0):
    d=js[bi][0].Dobj; k=0
    while d is not None and k<2:
        m=d.Mobj; mat=m.Material
        print('BONE',bi,'dobj',k,'RenderFlags',m.RenderFlags,'| amb',mat.AMB_R,mat.AMB_G,mat.AMB_B,mat.AMB_A,'dif',mat.DIF_R,mat.DIF_G,mat.DIF_B,mat.DIF_A,'spc',mat.SPC_R,mat.SPC_G,mat.SPC_B,'alpha',mat.Alpha,'shin',mat.Shininess,'| pe',m.PEDesc is not None)
        tx=m.Textures
        while tx is not None:
            print('   TOBJ',tx.Flags,'wrapS',tx.WrapS,'wrapT',tx.WrapT,'fmt',tx.ImageData.Format,tx.ImageData.Width,tx.ImageData.Height,'mag',tx.MagFilter,'lod',tx.LOD is not None,'tlut',tx.TlutData is not None, 'SX',tx.SX,'blend',tx.Blending,'texmap',tx.TexMapID,'gxsrc',tx.GXTexGenSrc)
            tx=tx.Next
        po=d.Pobj
        print('   POBJ flags',po.Flags,'attrs',[(str(a.AttributeName),str(a.AttributeType),str(a.CompCount),str(a.CompType),a.Scale,a.Stride) for a in po.ToGXAttributes()] if hasattr(po,'ToGXAttributes') else '')
        d=d.Next; k+=1
