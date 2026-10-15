"""Render the original keystroke/motion mark; deterministic, font independent."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

out=Path(__file__).resolve().parents[1]/'assets';out.mkdir(exist_ok=True)
scale=3;n=1024*scale
image=Image.new('RGBA',(n,n),(0,0,0,0))
d=ImageDraw.Draw(image)
def rect(box,r,fill):d.rounded_rectangle(tuple(int(v*scale) for v in box),radius=r*scale,fill=fill)
rect((40,40,984,984),212,'#111914')
rect((48,48,976,976),206,'#435C49')
rect((60,60,964,964),196,'#17231B')
rect((116,116,908,908),146,'#ACD5AE')
# Subtle daylight shading inside the keycap.
mask=Image.new('L',(n,n),0);md=ImageDraw.Draw(mask);md.rounded_rectangle((116*scale,116*scale,908*scale,908*scale),radius=146*scale,fill=255)
wash=Image.new('RGBA',(n,n));wd=ImageDraw.Draw(wash)
for y in range(116*scale,909*scale):
    t=(y/scale-116)/792
    wd.line((116*scale,y,908*scale,y),fill=(235,255,235,round(35*(1-t))))
wash.putalpha(Image.composite(wash.getchannel('A'),Image.new('L',(n,n),0),mask));image=Image.alpha_composite(image,wash);d=ImageDraw.Draw(image)
rect((240,298,610,366),34,'#17271C')
rect((240,462,495,530),34,'#17271C')
rect((240,626,390,694),34,'#17271C')
# The final keystroke becomes a motion arrow.
points=[(496,664),(709,451),(613,451),(613,379),(832,379),(832,598),(760,598),(760,502),(547,715)]
d.polygon([(x*scale,y*scale) for x,y in points],fill='#17271C')
image=image.resize((1024,1024),Image.Resampling.LANCZOS)
image.save(out/'icon.png');image.save(out/'icon.ico',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
image.save(out/'icon.icns')
# Branded drag-to-install canvas, with native Finder icons placed in the circles.
bg=Image.new('RGB',(1280,840),'#141816');draw=ImageDraw.Draw(bg)
from PIL import ImageFont
font_path=Path('/System/Library/Fonts/SFNS.ttf')
if not font_path.exists():font_path=Path('C:/Windows/Fonts/segoeui.ttf')
def font(size):return ImageFont.truetype(str(font_path),size) if font_path.exists() else ImageFont.load_default(size=size)
draw.text((80,56),'AutoTyper Pro',font=font(44),fill='#F0F3EF')
draw.text((82,116),'INSTALL  /  macOS',font=font(17),fill='#ACD5AE')
for x in (350,930):draw.ellipse((x-120,340-120,x+120,340+120),fill='#1D2921',outline='#3A5140',width=2)
for x in (350,930):draw.rounded_rectangle((x-108,458,x+108,504),radius=16,fill='#ACD5AE')
draw.line((520,340,760,340),fill='#ACD5AE',width=4)
draw.line((740,324,760,340,740,356),fill='#ACD5AE',width=4)
draw.text((640,570),'Drag AutoTyper Pro to Applications',font=font(31),fill='#F0F3EF',anchor='mm')
draw.text((640,627),'Then open it from Applications to get started.',font=font(21),fill='#97A79C',anchor='mm')
draw.text((80,738),'LOCAL TOOLS. YOUR RHYTHM.',font=font(16),fill='#97A79C')
bg.save(out/'dmg-background.png')

# Native status item: the established mark without the app-icon keycap.
menu_scale=4
menu=Image.new('RGBA',(18*menu_scale,18*menu_scale),(0,0,0,0))
md=ImageDraw.Draw(menu)
def menu_line(points,width=1.8):
    md.line([(round(x*menu_scale),round(y*menu_scale)) for x,y in points],fill=(0,0,0,255),width=round(width*menu_scale),joint='curve')
for y,end in ((4,9),(8,7),(12,5)):
    md.rounded_rectangle((2*menu_scale,round((y-.8)*menu_scale),end*menu_scale,round((y+.8)*menu_scale)),radius=menu_scale,fill=(0,0,0,255))
menu_line([(8,15),(15,8)])
menu_line([(10,8),(15,8),(15,13)])
menu.save(out/'menubar-template.png')
