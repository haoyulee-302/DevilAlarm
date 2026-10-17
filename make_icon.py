from pathlib import Path
from PIL import Image, ImageDraw


def make_icon():
    image = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((16, 16, 496, 496), radius=110, fill='#151D2D')
    draw.polygon(((125, 172), (93, 79), (211, 133)), fill='#FF765E')
    draw.polygon(((387, 172), (419, 79), (301, 133)), fill='#FF765E')
    draw.ellipse((107, 122, 405, 420), outline='#FF765E', width=26)
    draw.line(((256, 190), (256, 274), (317, 305)), fill='#EDF2FA', width=24)
    draw.ellipse((240, 258, 272, 290), fill='#EDF2FA')
    draw.line(((165, 416), (144, 449)), fill='#FF765E', width=22)
    draw.line(((347, 416), (368, 449)), fill='#FF765E', width=22)
    path = Path(__file__).with_name('app.ico')
    image.save(path, sizes=[(16,16), (24,24), (32,32), (48,48), (64,64), (128,128), (256,256)])


if __name__ == '__main__':
    make_icon()
