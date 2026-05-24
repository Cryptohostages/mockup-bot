import os
import io
from PIL import Image, ImageDraw, ImageFilter
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

TOKEN = os.environ.get("BOT_TOKEN", "")
PHOTO, ZOOM, OFFSET, DI = range(4)

def make_mockup(screenshot, zoom, offset, show_di):
    SIZE = 1080
    scale = zoom / 100
    offset_pct = offset / 100

    bg = Image.new("RGB", (SIZE, SIZE))
    draw = ImageDraw.Draw(bg)
    for y in range(SIZE):
        t = y / SIZE
        r = int(144*(1-t) + 25*t)
        g = int(212*(1-t) + 133*t)
        b = int(255*(1-t) + 192*t)
        draw.line([(0,y),(SIZE,y)], fill=(r,g,b))

    phone_h = SIZE * 0.88 * scale
    phone_w = phone_h * 0.461
    px = (SIZE - phone_w) / 2
    py = (SIZE - phone_h) / 2 + offset_pct * SIZE

    R1 = phone_w * 0.145
    t1 = phone_w * 0.018
    R2 = phone_w * 0.128
    t2 = phone_w * 0.022
    R3 = phone_w * 0.115

    canvas = bg.convert("RGBA")

    shadow = Image.new("RGBA", (SIZE,SIZE), (0,0,0,0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [px+4, py+36, px+phone_w+4, py+phone_h+36],
        radius=R1, fill=(0,0,0,100))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    canvas = Image.alpha_composite(canvas, shadow)

    shell = Image.new("RGBA", (SIZE,SIZE), (0,0,0,0))
    ImageDraw.Draw(shell).rounded_rectangle(
        [px, py, px+phone_w, py+phone_h],
        radius=R1, fill=(210,228,245,235))
    canvas = Image.alpha_composite(canvas, shell)

    bx=px+t1; by=py+t1; bw=phone_w-t1*2; bh=phone_h-t1*2
    bezel = Image.new("RGBA", (SIZE,SIZE), (0,0,0,0))
    ImageDraw.Draw(bezel).rounded_rectangle(
        [bx,by,bx+bw,by+bh], radius=R2, fill=(13,13,13,255))
    canvas = Image.alpha_composite(canvas, bezel)

    sx=bx+t2; sy=by+t2; sw=bw-t2*2; sh=bh-t2*2

    ia = screenshot.width / screenshot.height
    sa = sw / sh
    if ia > sa:
        new_h=int(sh); new_w=int(new_h*ia)
    else:
        new_w=int(sw); new_h=int(new_w/ia)

    ss = screenshot.convert("RGBA").resize((new_w,new_h), Image.LANCZOS)
    dx = int((new_w-sw)/2)
    ss_crop = ss.crop((dx, 0, dx+int(sw), int(sh)))

    scr_mask = Image.new("L", (int(sw),int(sh)), 0)
    ImageDraw.Draw(scr_mask).rounded_rectangle(
        [0,0,int(sw),int(sh)], radius=int(R3), fill=255)
    screen_layer = Image.new("RGBA", (SIZE,SIZE), (0,0,0,0))
    screen_layer.paste(ss_crop, (int(sx),int(sy)), scr_mask)
    canvas = Image.alpha_composite(canvas, screen_layer)

    if show_di:
        di_w=sw*0.293; di_h=sw*0.086
        di_x=sx+(sw-di_w)/2; di_y=sy+sh*0.012
        di_layer = Image.new("RGBA", (SIZE,SIZE), (0,0,0,0))
        ImageDraw.Draw(di_layer).rounded_rectangle(
            [di_x,di_y,di_x+di_w,di_y+di_h],
            radius=di_h/2, fill=(0,0,0,255))
        canvas = Image.alpha_composite(canvas, di_layer)

    canvas = canvas.crop((0,0,SIZE,SIZE))
    out = io.BytesIO()
    canvas.convert("RGB").save(out, format="PNG")
    out.seek(0)
    return out

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Отправь скриншот с iPhone:")
    return PHOTO

async def got_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    ctx.user_data["photo"] = await file.download_as_bytearray()
    await update.message.reply_text(
        "🔍 Зум? (60–150)\n95 = весь телефон, 120–140 = выходит за край",
        reply_markup=ReplyKeyboardMarkup(
            [["95"],["110"],["125"],["140"]],
            one_time_keyboard=True, resize_keyboard=True))
    return ZOOM

async def got_zoom(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["zoom"] = max(60, min(150, int(update.message.text.strip())))
    except:
        await update.message.reply_text("Введи число, например 110")
        return ZOOM
    await update.message.reply_text(
        "↕️ Офсет? (0–60)\n0 = по центру, 30–40 = выходит снизу",
        reply_markup=ReplyKeyboardMarkup(
            [["0"],["20"],["35"],["50"]],
            one_time_keyboard=True, resize_keyboard=True))
    return OFFSET

async def got_offset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["offset"] = max(0, min(60, int(update.message.text.strip())))
    except:
        await
