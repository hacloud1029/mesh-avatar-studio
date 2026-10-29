# Paints the drawn eye / mouth variants into projects/sheep/variants/ (full-size, edits inside masks only).
import json, math, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
d='projects/sheep/'; S=4
src=np.asarray(Image.open(d+'source.png').convert('RGBA')).copy()
base=np.asarray(Image.open(d+'built/base.png').convert('RGBA')).copy()
rig=json.load(open(d+'rig.json')); H,W=src.shape[:2]
os.makedirs(d+'variants',exist_ok=True)
LASH=(28,16,12,255); LINE=(62,24,18,255); INSIDE=(96,28,34,255); TONGUE=(226,112,112,255); TEETH=(250,244,232,255)

def poly(pts,dil=0):
    m=np.zeros((H,W),np.uint8); cv2.fillPoly(m,[np.int32(np.round(pts))],255)
    if dil: m=cv2.dilate(m,np.ones((dil,dil),np.uint8))
    return m>0
def layer(draw_fn):
    """Supersampled RGBA layer drawn by draw_fn(ImageDraw, s) -> numpy RGBA (premult-free)."""
    im=Image.new('RGBA',(W*S,H*S),(0,0,0,0)); draw_fn(ImageDraw.Draw(im),lambda v:v*S, im)
    return np.asarray(im.resize((W,H),Image.LANCZOS)).astype(float)
def over(dst,lay):
    a=lay[...,3:4]/255; out=dst.astype(float).copy()
    out[...,:3]=lay[...,:3]*a+out[...,:3]*(1-a); out[...,3]=np.maximum(out[...,3],lay[...,3]); return out.astype(np.uint8)
def stroke(g,s,pts,w0,w1,col):
    """Tapered stroke: width w0 at ends, w1 in the middle."""
    n=len(pts)
    for i in range(n-1):
        t=i/(n-2) if n>2 else 0; w=w0+(w1-w0)*math.sin(math.pi*t)
        (x0,y0),(x1,y1)=pts[i],pts[i+1]; r=w/2
        g.line([(s(x0),s(y0)),(s(x1),s(y1))],fill=col,width=max(1,int(s(w))))
        g.ellipse([s(x1-r),s(y1-r),s(x1+r),s(y1+r)],fill=col)
def curve(p0,p1,p2,n=40):
    return [((1-t)**2*p0[0]+2*t*(1-t)*p1[0]+t*t*p2[0],(1-t)**2*p0[1]+2*t*(1-t)*p1[1]+t*t*p2[1]) for t in np.linspace(0,1,n)]

EYES=[dict(c=(375,498),xo=331,xi=419,outer=-1),dict(c=(621,498),xo=663,xi=577,outer=1)]
openings=[poly(e['opening']) for e in rig['eyes']]
emask=np.asarray(Image.open(d+'variant-requests/eyes_closed/mask.png').convert('RGBA'))[...,3]<128
emask=cv2.erode(emask.astype(np.uint8),np.ones((9,9),np.uint8))>0
yy,xx=np.mgrid[:H,:W]; lum=src[...,:3].mean(-1)
dk=((lum<150)&(yy>400)&(yy<480)).astype(np.uint8)
_,lab=cv2.connectedComponents(dk,connectivity=4)
ids=np.unique(lab[(yy<440)&(dk>0)]); ids=ids[ids>0]
brow=cv2.dilate(np.isin(lab,ids).astype(np.uint8),np.ones((3,3),np.uint8))>0
def skin_patch():
    """Smooth eyelid skin: quadratic fit to the skin ring around each eye, feathered into the source."""
    out=src.astype(float).copy()
    for e in rig['eyes']:
        R=poly(e['roi'],9)&emask&~brow
        ring=(cv2.dilate(R.astype(np.uint8),np.ones((31,31),np.uint8))>0)&~R&~brow&(lum>150)&(src[...,3]>250)
        ry,rx=np.where(ring); X=np.stack([np.ones_like(rx),rx,ry,rx*rx,rx*ry,ry*ry],1).astype(float)
        sc=np.array([1,1e-2,1e-2,1e-4,1e-4,1e-4]); X=X*sc
        fy,fx=np.where(R); Xf=np.stack([np.ones_like(fx),fx,fy,fx*fx,fx*fy,fy*fy],1).astype(float)*sc
        fill=np.zeros((len(fy),3))
        for c in range(3):
            coef,*_=np.linalg.lstsq(X,src[ry,rx,c].astype(float),rcond=None); fill[:,c]=Xf@coef
        rng=np.random.default_rng(0); fill+=rng.normal(0,1.2,(len(fy),1))
        alpha=cv2.GaussianBlur(cv2.erode(R.astype(np.uint8)*255,np.ones((5,5),np.uint8)),(0,0),2.5)/255.0
        a=alpha[fy,fx][:,None]; out[fy,fx,:3]=fill*a+out[fy,fx,:3]*(1-a)
    return np.clip(out,0,255).astype(np.uint8)
skin=skin_patch()
eye_region=[poly(e['roi'],9)&emask&~brow for e in rig['eyes']]

def skin_eyes(img):
    return skin.copy()
def save(name,img): Image.fromarray(img).save(d+f'variants/{name}.png'); print('wrote',name)

# ---- eyes_closed: relaxed closed lash line sagging downward, with the outer flick
def closed(g,s,im):
    for e in EYES:
        cx,cy=e['c']; xo,xi=e['xo'],e['xi']
        pts=curve((xo-4,506),((xo+xi)/2,522),(xi+2,508))
        stroke(g,s,pts,2.5,7.5,LASH)
        fx=xo+e['outer']*12  # flick outward-up
        stroke(g,s,curve((xo-e['outer']*2,507),(xo+e['outer']*6,503),(fx,496),12),2,4.5,LASH)
save('eyes_closed',over(skin_eyes(src),layer(closed)))

# ---- eyes_smile: happy upward arcs ^ ^
def smile(g,s,im):
    for e in EYES:
        xo,xi=e['xo'],e['xi']; m=(xo+xi)/2
        stroke(g,s,curve((xo-2,516),(m,476),(xi+2,516)),3,8,LASH)
save('eyes_smile',over(skin_eyes(src),layer(smile)))

# ---- lidded eyes: cover above a lid line with skin and draw a heavy lash on it
def lidded(lid, name, extra=None):
    out=src.copy(); yy,xx=np.mgrid[:H,:W]
    lay_pts=[]
    for i,e in enumerate(EYES):
        xs=np.arange(W); ly=np.array([lid(i,x) for x in xs])
        cover=eye_region[i]&(yy<ly[xx]+1)
        out[cover]=skin[cover]
        x0,x1=sorted((e['xo']-3,e['xi']+3)); pts=[(x,lid(i,x)) for x in np.linspace(x0,x1,40)]
        lay_pts.append((e,pts))
    def dr(g,s,im):
        for e,pts in lay_pts:
            stroke(g,s,pts,3,8,LASH)
            end=pts[0] if e['outer']<0 else pts[-1]
            stroke(g,s,curve(end,(end[0]+e['outer']*7,end[1]-3),(end[0]+e['outer']*12,end[1]-9),12),2,4.5,LASH)
        if extra: extra(g,s,im)
    save(name,over(out,layer(dr)))

def u(i,x):  # -1 at outer corner .. +1 at inner corner
    e=EYES[i]; return (x-e['xo'])/(e['xi']-e['xo'])*2-1
# half-lidded: flat heavy lid across the middle of the eye
lidded(lambda i,x: 494-5*(1-u(i,x)**2), 'eyes_half')
# sad: inner corner raised, outer corner drooping, plus a teary shine on the lower lid
def tears(g,s,im):
    for e in EYES:
        xo,xi=e['xo'],e['xi']
        pts=curve((xo+e['outer']*-8,526),((xo+xi)/2,540),(xi-e['outer']*-6,524),30)
        stroke(g,s,pts,1.5,4,(235,245,255,200))
        cx=(xo+xi)/2; g.ellipse([s(cx-9),s(532-3),s(cx+9),s(532+3)],fill=(255,255,255,170))
lidded(lambda i,x: 487-15*u(i,x)-3*(1-u(i,x)**2), 'eyes_sad', tears)

# ---- eyes_surprise: lots of eye white, small irises and pupils
def surprise_img():
    out=src.copy()
    for i,(e,op) in enumerate(zip(EYES,openings)):
        ys,xs=np.where(op); cx,cy=xs.mean(),ys.mean()
        inner=cv2.erode(op.astype(np.uint8),np.ones((3,3),np.uint8))>0
        shade=np.clip((np.mgrid[:H,:W][0]-ys.min())/(ys.max()-ys.min()),0,1)
        white=np.stack([236+12*shade,230+12*shade,222+14*shade,np.full_like(shade,255)],-1).astype(np.uint8)
        out[inner]=white[inner]
    def dr(g,s,im):
        for i,(e,op) in enumerate(zip(EYES,openings)):
            ys,xs=np.where(op); cx,cy=xs.mean()+e['outer']*-3,ys.mean()+2
            for r,col in ((21,(70,38,22,255)),(19,(120,70,36,255)),(9,(14,8,6,255))):
                g.ellipse([s(cx-r),s(cy-r*1.08),s(cx+r),s(cy+r*1.08)],fill=col)
            g.ellipse([s(cx-12),s(cy-14),s(cx-4),s(cy-6)],fill=(255,255,255,255))
            g.ellipse([s(cx+6),s(cy+7),s(cx+10),s(cy+11)],fill=(255,255,255,200))
    return over(out,layer(dr))
save('eyes_surprise',surprise_img())

# ---- mouths: remove the drawn mouth (keep the philtrum above y 600), then paint
mm=np.asarray(Image.open(d+'variant-requests/mouth_a/mask.png').convert('RGBA'))[...,3]<128
edit=cv2.erode(mm.astype(np.uint8),np.ones((9,9),np.uint8))>0
yy,xx=np.mgrid[:H,:W]; lum=src[...,:3].mean(-1)
dark=(lum<150)&edit&~((abs(xx-493)<6)&(yy<603))
dark=cv2.dilate(dark.astype(np.uint8),np.ones((5,5),np.uint8))
clean=src.copy(); clean[...,:3]=cv2.inpaint(np.ascontiguousarray(src[...,:3]),dark,7,cv2.INPAINT_TELEA)
CX=493
PX=494
def mouth(name,top,bottom,tongue=None,teeth=False):
    """top: (left corner, apex, right corner) of the upper line; bottom: control y of the lower curve."""
    L,A,R=top
    def dr(g,s,im):

        upper=[L]+curve(L,((L[0]+A[0])/2,A[1]+1),A,12)[1:]+curve(A,((A[0]+R[0])/2,A[1]+1),R,12)[1:]
        lower=curve(R,(CX,bottom),L,30)
        shape=[(s(x),s(y)) for x,y in upper+lower]
        g.polygon(shape,fill=INSIDE)
        sh=Image.new('L',im.size,0); ImageDraw.Draw(sh).polygon(shape,fill=255)
        dk=Image.new('RGBA',im.size,(45,10,16,0)); grad=Image.linear_gradient('L').resize(im.size).point(lambda v: int(max(0,150-v*2.2)))
        dk.putalpha(Image.composite(grad,Image.new('L',im.size,0),sh)); im.alpha_composite(dk)
        if teeth:
            tb=[(x,y+8) for x,y in upper]
            sh2=Image.new('L',im.size,0); ImageDraw.Draw(sh2).polygon(shape,fill=255)
            t=Image.new('RGBA',im.size,(0,0,0,0)); ImageDraw.Draw(t).polygon([(s(x),s(y)) for x,y in upper+tb[::-1]],fill=TEETH)
            im.alpha_composite(Image.composite(t,Image.new('RGBA',im.size,(0,0,0,0)),sh2))
        if tongue:
            tx,ty,trx,tr=tongue
            mask=Image.new('L',im.size,0); ImageDraw.Draw(mask).polygon(shape,fill=255)
            t=Image.new('RGBA',im.size,(0,0,0,0)); td=ImageDraw.Draw(t)
            td.ellipse([s(tx-trx),s(ty-tr),s(tx+trx),s(ty+tr)],fill=TONGUE)
            td.line([(s(tx),s(ty-tr*0.6)),(s(tx),s(ty+tr*0.4))],fill=(200,85,90,255),width=int(s(1.5)))
            im.alpha_composite(Image.composite(t,Image.new('RGBA',im.size,(0,0,0,0)),mask))
        stroke(g,s,upper,2.5,4,LINE); stroke(g,s,lower,2.5,3.5,LINE)
        stroke(g,s,[(PX,594),(A[0],A[1])],3.5,3.5,LINE)
    save(name,over(clean,layer(dr)))
mouth('mouth_a',((431,614),(493,599),(555,614)),730,tongue=(493,662,38,17))
mouth('mouth_a_half',((436,613),(493,601),(550,613)),690,tongue=(493,644,30,12))
mouth('mouth_i',((427,614),(493,603),(559,614)),654,teeth=True)
def mouth_o(g,s,im):
    g.ellipse([s(CX-31),s(602),s(CX+31),s(674)],fill=INSIDE)
    g.ellipse([s(CX-20),s(648),s(CX+20),s(670)],fill=TONGUE)
    g.arc([s(CX-31),s(602),s(CX+31),s(674)],0,360,fill=LINE,width=int(s(4)))
    stroke(g,s,[(PX,594),(CX,604)],3.5,3.5,LINE)
save('mouth_o',over(clean,layer(mouth_o)))
def closed_mouth(name,pts_fn,w):
    def dr(g,s,im):
        stroke(g,s,[(PX,594),(CX,min(y for x,y in pts_fn())+1)],3.5,3.5,LINE)
        stroke(g,s,pts_fn(),2.5,w,LINE)
    save(name,over(clean,layer(dr)))
closed_mouth('mouth_angry',lambda: [(440,642)]+curve((440,642),(466,614),(493,606),12)[1:]+curve((493,606),(520,614),(546,642),12)[1:],6)
closed_mouth('mouth_sad',lambda: [(446,636)]+curve((446,636),(469,608),(493,611),10)[1:]+curve((493,611),(517,608),(540,636),10)[1:],5)
