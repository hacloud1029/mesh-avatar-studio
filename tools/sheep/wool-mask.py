# Replaces built/hairmask.png with a smooth wool + ear mask (the automatic one is patchy on wool).
# Re-run after every "Save and rebuild layers":
#   uv run --with numpy --with pillow --with opencv-python-headless projects/sheep/work/wool-mask.py
import numpy as np, cv2
from PIL import Image
d='projects/sheep/'
a=np.asarray(Image.open(d+'source.png').convert('RGBA'))
h,w=a.shape[:2]; yy,xx=np.mgrid[:h,:w]
rgb=a[...,:3].astype(int); lum=rgb.mean(axis=2)
opaque=a[...,3]>200
face=((xx-505)/235)**2+((yy-515)/172)**2<=1
horn=(lum<150)&(rgb[...,0]-rgb[...,2]>25)&(yy<330)&((xx<300)|(xx>700))
glasses=lum<70
bad=cv2.dilate((horn|glasses).astype(np.uint8),np.ones((9,9),np.uint8))>0
m=(opaque&~face&~bad&(yy<720)).astype(np.uint8)*255
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
m=cv2.GaussianBlur(m,(0,0),6)
m[(a[...,3]==0)]=0
Image.fromarray(m).save(d+'built/hairmask.png')
print('wool mask written')
