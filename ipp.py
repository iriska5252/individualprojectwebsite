from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw
import base64
import io
import hashlib
import random

app = Flask(__name__)

def generate_color_from_hash(hash_value: str, index: int) -> tuple:
    """Генерирует цвет на основе хеша и индекса"""
    # Используем разные части хеша для разных каналов
    h = hashlib.md5(f"{hash_value}{index}".encode()).hexdigest()
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return (r, g, b)

def encode_password_to_image(password: str) -> io.BytesIO:
    # Создаем хеш пароля для детерминированной генерации
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Создаем изображение 500x500
    img = Image.new("RGB", (500, 500), color="green")
    draw = ImageDraw.Draw(img)
    
    # Размер ячейки для узора
    cell_size = 50  # 500/50 = 10x10 ячеек
    
    # Генерируем уникальный узор на основе пароля
    random.seed(password_hash)  # Фиксируем seed для воспроизводимости
    
    for i in range(0, 500, cell_size):
        for j in range(0, 500, cell_size):
            # Создаем уникальный индекс для каждой ячейки
            cell_index = (i // cell_size) * 10 + (j // cell_size)
            
            # Основной цвет ячейки на основе хеша
            main_color = generate_color_from_hash(password_hash, cell_index)
            
            # Рисуем прямоугольник с градиентом или узором
            for x in range(cell_size):
                for y in range(cell_size):
                    # Модифицируем цвет для создания градиента или текстуры
                    variation = (x + y) % 30
                    r = min(255, main_color[0] + variation - 15)
                    g = min(255, main_color[1] + variation - 15)
                    b = min(255, main_color[2] + variation - 15)
                    
                    # Убеждаемся, что значения в пределах 0-255
                    r = max(0, min(255, r))
                    g = max(0, min(255, g))
                    b = max(0, min(255, b))
                    
                    draw.point((i + x, j + y), fill=(r, g, b))
            
            # Добавляем случайные геометрические фигуры для разнообразия
            if random.random() > 0.7:
                # Рисуем круг или овал
                center_x = i + cell_size // 2
                center_y = j + cell_size // 2
                radius = cell_size // 4
                circle_color = generate_color_from_hash(password_hash, cell_index + 100)
                draw.ellipse(
                    [center_x - radius, center_y - radius, 
                     center_x + radius, center_y + radius],
                    fill=circle_color
                )
    
    # Добавляем базовый узор из закодированных данных
    encoded = base64.b64encode(password.encode("utf-8"))
    data = list(encoded)
    
    # Используем данные для создания дополнительного узора
    for idx, byte in enumerate(data):
        x = (idx * 10) % 500
        y = ((idx * 10) // 500) * 10
        if y < 500:
            color = (byte, 255 - byte, (byte * 2) % 255)
            draw.rectangle([x, y, x+5, y+5], fill=color)
    
    # Сохраняем изображение
    img_io = io.BytesIO()
    img.save(img_io, format="PNG")
    img_io.seek(0)
    return img_io

def decode_image_to_password(image_file) -> str:
    """Декодирует пароль из изображения"""
    img = Image.open(image_file)
    pixels = list(img.getdata())
    
    # Извлекаем данные из синих пикселей в определенных позициях
    bytes_list = []
    for idx, pixel in enumerate(pixels[:100]):  # Берем первые 100 пикселей
        if idx % 10 == 0:  # Берем каждый 10-й пиксель
            bytes_list.append(pixel[0])  # Берем красный канал
    
    try:
        decoded_bytes = bytes(bytes_list[:len(bytes_list)//10*10])  # Обрезаем до кратного размера
        return base64.b64decode(decoded_bytes).decode("utf-8")
    except:
        # Если не удалось декодировать, пробуем другой метод
        bytes_list = [pixel[0] for pixel in pixels[:50]]  # Берем первые 50 пикселей
        try:
            return base64.b64decode(bytes(bytes_list)).decode("utf-8")
        except:
            raise Exception("Не удалось декодировать пароль из изображения")


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/encode", methods=["POST"])
def encode():
    password = request.form.get("password")
    
    if not password:
        return "Пароль не может быть пустым", 400
    
    try:
        image = encode_password_to_image(password)
        return send_file(
            image,
            mimetype="image/png",
            as_attachment=True,
            download_name="password_image.png"
        )
    except Exception as e:
        return f"Ошибка кодирования: {str(e)}", 400

@app.route("/decode", methods=["POST"])
def decode():
    file = request.files.get("image")
    
    if not file:
        return "Файл не выбран", 400
    
    try:
        password = decode_image_to_password(file)
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Результат декодирования</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }}
                .result {{
                    text-align: center;
                    background: rgba(0,0,0,0.7);
                    padding: 30px;
                    border-radius: 15px;
                    font-size: 20px;
                }}
                a {{
                    display: inline-block;
                    margin-top: 100px;
                    color: #fff;
                    text-decoration: none;
                    background: #667eea;
                    padding: 10px 100px;
                    border-radius: 15px;
                }}
                a:hover {{
                    background: #5a67d8;
                }}
            </style>
        </head>
        <body>
            <div class="result">
                Расшифрованный пароль: <strong>{password}</strong><br>
                <a href="/">Вернуться на главную</a>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        return f"Ошибка декодирования: {str(e)}", 400

if __name__ == "__main__":
    app.run(debug=True)
