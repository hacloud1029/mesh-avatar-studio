# Rebuilds built/base.png around each eye: original pixels for the lid/socket skin, and smooth
# fitted skin only where the eye layers (ball, lash, lower lid, crease) sit. Re-run after rebuilding layers.
import json, numpy as np, cv2
from PIL import Image
d='projects/sheep/'
src=np.asarray(Image.open(d+'source.png').convert('RGBA')).astype(float)
base=np.asarray(Image.open(d+'built/base.png').convert('RGBA')).astype(float)
rig=json.load(open(d+'rig.json')); L=json.load(open(d+'built/layers.json'))['layers']
H,W=src.shape[:2]; lum=src[...,:3].mean(-1)
def poly(pts,dil=0):
    m=np.zeros((H,W),np.uint8); cv2.fillPoly(m,[np.int32(np.round(pts))],255)
    return cv2.dilate(m,np.ones((dil,dil),np.uint8))>0 if dil else m>0
out=base.copy()
for i,e in enumerate(rig['eyes']):
    roi=poly(e['roi'],7)
    content=poly(e['opening'])
    for part in ('ball','lash','low','crease'):
        x,y,w,h=L[f'eye{i}_{part}']; a=np.asarray(Image.open(d+f'built/eye{i}_{part}.png').convert('RGBA'))[...,3]
        content[y:y+h,x:x+w]|=a>20
    content=cv2.dilate(content.astype(np.uint8),np.ones((5,5),np.uint8))>0
    # skin samples: roi pixels that are neither eye content nor dark lines
    ring=roi&~content&(lum>150)
    ry,rx=np.where(ring); sc=np.array([1,1e-2,1e-2,1e-4,1e-4,1e-4])
    X=np.stack([np.ones_like(rx),rx,ry,rx*rx,rx*ry,ry*ry],1)*sc
    fy,fx=np.where(roi)
    Xf=np.stack([np.ones_like(fx),fx,fy,fx*fx,fx*fy,fy*fy],1)*sc
    fill=np.stack([Xf@np.linalg.lstsq(X,src[ry,rx,c],rcond=None)[0] for c in range(3)],1)
    # weight: 1 inside eye content, 0 on plain skin, soft 3px edge
    wgt=cv2.GaussianBlur(content.astype(np.float32),(0,0),1.5)[fy,fx][:,None]
    pix=src[fy,fx,:3]*(1-wgt)+fill*wgt
    out[fy,fx,:3]=pix; out[fy,fx,3]=src[fy,fx,3]
Image.fromarray(np.clip(out,0,255).astype(np.uint8)).save(d+'built/base.png'); print('base eyes rebuilt')
