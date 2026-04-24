from flask import Flask, render_template, request
from PIL import Image, ImageDraw
import base64
import io
import hashlib
import random

app = Flask(__name__)


def generate_color_from_hash(hash_value: str, index: int) -> tuple[int, int, int]:
    """Генерирует цвет на основе хеша и индекса."""
    h = hashlib.md5(f"{hash_value}{index}".encode()).hexdigest()
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def encode_password_to_image(password: str) -> bytes:
    """Кодирует пароль в PNG-изображение и возвращает байты файла."""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    img = Image.new("RGB", (500, 500), color="green")
    draw = ImageDraw.Draw(img)
    cell_size = 50

    random.seed(password_hash)

    for i in range(0, 500, cell_size):
        for j in range(0, 500, cell_size):
            cell_index = (i // cell_size) * 10 + (j // cell_size)
            main_color = generate_color_from_hash(password_hash, cell_index)

            for x in range(cell_size):
                for y in range(cell_size):
                    variation = (x + y) % 30
                    r = max(0, min(255, main_color[0] + variation - 15))
                    g = max(0, min(255, main_color[1] + variation - 15))
                    b = max(0, min(255, main_color[2] + variation - 15))
                    draw.point((i + x, j + y), fill=(r, g, b))

            if random.random() > 0.7:
                center_x = i + cell_size // 2
                center_y = j + cell_size // 2
                radius = cell_size // 4
                circle_color = generate_color_from_hash(password_hash, cell_index + 100)
                draw.ellipse(
                    [
                        center_x - radius,
                        center_y - radius,
                        center_x + radius,
                        center_y + radius,
                    ],
                    fill=circle_color,
                )

    encoded = base64.b64encode(password.encode("utf-8"))
    for idx, byte in enumerate(encoded):
        x = (idx * 10) % 500
        y = ((idx * 10) // 500) * 10
        if y < 500:
            color = (byte, 255 - byte, (byte * 2) % 255)
            draw.rectangle([x, y, x + 5, y + 5], fill=color)

    img_io = io.BytesIO()
    img.save(img_io, format="PNG")
    return img_io.getvalue()


def decode_image_to_password(image_file) -> str:
    """Декодирует пароль из изображения на основе записанных пикселей."""
    img = Image.open(image_file).convert("RGB")
    bytes_list = []

    for idx in range(0, 500, 10):
        x = (idx * 10) % 500
        y = ((idx * 10) // 500) * 10
        if y < 500:
            r, _g, _b = img.getpixel((x, y))
            bytes_list.append(r)

    try:
        return base64.b64decode(bytes(bytes_list), validate=True).decode("utf-8")
    except Exception as exc:
        raise ValueError("Не удалось декодировать пароль из изображения") from exc


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/password", methods=["GET", "POST"])
def password_page():
    image_data = None
    error = None

    if request.method == "POST":
        password = request.form.get("password", "")

        if not (4 <= len(password) <= 15):
            error = "Пароль должен быть от 4 до 15 символов."
        else:
            image_bytes = encode_password_to_image(password)
            image_data = base64.b64encode(image_bytes).decode("utf-8")

    return render_template("password.html", image_data=image_data, error=error)


@app.route("/image", methods=["GET", "POST"])
def image_page():
    password = ""
    error = None

    if request.method == "POST":
        file = request.files.get("image")
        if not file:
            error = "Файл не выбран."
        else:
            try:
                password = decode_image_to_password(file)
            except ValueError as exc:
                error = str(exc)

    return render_template("image.html", decoded_password=password, error=error)


if __name__ == "__main__":
    app.run(debug=True)
