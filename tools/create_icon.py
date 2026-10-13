"""Generate the project's original app icon using Pillow."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path(__file__).resolve().parents[1] / 'assets'
out.mkdir(exist_ok=True)
image = Image.new('RGBA', (1024,1024), (0,0,0,0))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((34,34,990,990),radius=220,fill='#141816')
draw.rounded_rectangle((115,115,909,909),radius=160,fill='#ACD5AE')
font_paths = ['/System/Library/Fonts/SFNS.ttf','C:/Windows/Fonts/segoeuib.ttf']
font = next((ImageFont.truetype(p,560) for p in font_paths if Path(p).exists()),ImageFont.load_default(size=560))
draw.text((212,130),'a',font=font,fill='#141816')
draw.line([(616,684),(811,489)],fill='#141816',width=45)
draw.line([(654,489),(811,489),(811,646)],fill='#141816',width=45)
image.save(out/'icon.png')
image.save(out/'icon.ico',sizes=[(16,16),(32,32),(64,64),(128,128),(256,256)])
image.save(out/'icon.icns',sizes=[(128,128),(256,256),(512,512),(1024,1024)])
