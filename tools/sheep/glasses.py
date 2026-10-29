# Draws the round wire glasses as an overlay layer: built/overlays/glasses.png
import json, math, os
from PIL import Image, ImageDraw, ImageFilter
d='projects/sheep/'; W=H=1000; S=4
A=(377,500); B=(619,500); R=104
im=Image.new('RGBA',(W*S,H*S),(0,0,0,0)); g=ImageDraw.Draw(im)
s=lambda v: v*S
def ring(c,r,w,col):
    g.ellipse([s(c[0]-r),s(c[1]-r),s(c[0]+r),s(c[1]+r)],outline=col,width=int(w*S))
def arc(c,r,a0,a1,w,col):
    g.arc([s(c[0]-r),s(c[1]-r),s(c[0]+r),s(c[1]+r)],a0,a1,fill=col,width=int(w*S))
# glass: faint tint and reflection streaks
glass=Image.new('RGBA',im.size,(0,0,0,0)); gg=ImageDraw.Draw(glass)
for c in (A,B):
    gg.ellipse([s(c[0]-R),s(c[1]-R),s(c[0]+R),s(c[1]+R)],fill=(255,255,255,14))
    for r,a0,a1,wd,al in ((R-14,200,235,6,70),(R-26,205,222,3,55),(R-12,20,40,4,40)):
        gg.arc([s(c[0]-r),s(c[1]-r),s(c[0]+r),s(c[1]+r)],a0,a1,fill=(255,255,255,al),width=int(wd*S))
im.alpha_composite(glass.filter(ImageFilter.GaussianBlur(S*1.2)))
rim=(22,22,25,255)
for c in (A,B):
    ring(c,R,6.5,rim)
    arc(c,R-2.2,195,260,1.6,(120,120,128,255))   # inner highlight
    arc(c,R+2.0,300,340,1.4,(95,95,100,255))
# bridge: shallow upward arch between the lenses
def pt(c,ang): return (c[0]+R*math.cos(math.radians(ang)), c[1]+R*math.sin(math.radians(ang)))
p0=pt(A,-18); p1=pt(B,198); mid=((p0[0]+p1[0])/2, min(p0[1],p1[1])-9)
pts=[]
for i in range(41):
    t=i/40; x=(1-t)**2*p0[0]+2*t*(1-t)*mid[0]+t*t*p1[0]; y=(1-t)**2*p0[1]+2*t*(1-t)*mid[1]+t*t*p1[1]; pts.append((s(x),s(y)))
g.line(pts,fill=rim,width=int(6*S),joint='curve')
g.line([(x,y-S*1.6) for x,y in pts[8:33]],fill=(120,120,128,255),width=int(1.4*S))
# nose pads with short arms
for c,sg in ((A,1),(B,-1)):
    q=pt(c,14 if sg>0 else 166); pad=(c[0]+sg*74, c[1]+20)
    g.line([(s(q[0]),s(q[1])),(s(pad[0]),s(pad[1]))],fill=rim,width=int(3*S))
    g.ellipse([s(pad[0]-6),s(pad[1]-9),s(pad[0]+6),s(pad[1]+9)],fill=(30,30,34,255))
    g.ellipse([s(pad[0]-3),s(pad[1]-6),s(pad[0]),s(pad[1]-1)],fill=(150,150,158,255))
# end pieces and temple stubs
for c,sg in ((A,-1),(B,1)):
    x=c[0]+sg*R
    g.rounded_rectangle([s(x-7),s(c[1]-8),s(x+7),s(c[1]+8)],radius=3*S,fill=(28,28,32,255))
    g.line([(s(x+3),s(c[1]-5)),(s(x+3),s(c[1]+3))],fill=(130,130,138,255),width=int(1.5*S))
    g.line([(s(x+sg*6),s(c[1]-2)),(s(x+sg*22),s(c[1]-4))],fill=rim,width=int(4*S))
out=im.resize((W,H),Image.LANCZOS)
os.makedirs(d+'built/overlays',exist_ok=True); out.save(d+'built/overlays/glasses.png')
json.dump({'overlays':[{'name':'glasses','file':'glasses.png','rigid':True}],'version':1},open(d+'built/overlays/overlays.json','w'),indent=2)
src=Image.open(d+'source.png').convert('RGBA'); bg=Image.new('RGBA',src.size,(90,90,90,255)); bg.alpha_composite(src); bg.alpha_composite(out)
bg.crop((240,370,760,660)).save(d+'work/glasses-preview.png'); print('glasses overlay written')
