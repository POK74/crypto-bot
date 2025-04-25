
from PIL import Image, ImageDraw, ImageFont

def lag_analysebilde(ticker, data_15m, data_1h, output_filnavn="analyse.png"):
    img = Image.new('RGB', (800, 1000), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)

    try:
        font_header = ImageFont.truetype("arial.ttf", 28)
        font_body = ImageFont.truetype("arial.ttf", 22)
    except:
        font_header = font_body = None  # fallback for system uten font

    y = 30
    draw.text((20, y), f"📊 Teknisk Analyse – {ticker}", fill="white", font=font_header)
    y += 50

    def write_block(title, data):
        nonlocal y
        draw.text((20, y), title, fill="lightblue", font=font_header)
        y += 40
        for key, value in data.items():
            draw.text((40, y), f"{key}: {value}", fill="white", font=font_body)
            y += 28
        y += 20

    write_block("15 Minutter", data_15m)
    write_block("1 Time", data_1h)

    draw.text((20, y), "✅ Signalvurdering og anbefaling:", fill="lightgreen", font=font_header)
    y += 40
    draw.text((40, y), "Trend, momentum, volum og strategi her ...", fill="white", font=font_body)

    img.save(output_filnavn)
    return output_filnavn
