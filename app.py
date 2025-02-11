# app.py
from flask import Flask, render_template, request, jsonify, send_file
import os
import qrcode
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Создаем папки если их нет
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def generate_qr(message_id):
    """Генерирует QR код для сообщения"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"{request.host_url}listen/{message_id}")
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    qr_path = os.path.join(app.config['UPLOAD_FOLDER'], f'qr_{message_id}.png')
    img.save(qr_path)
    return qr_path

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'audio' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Проверка размера файла
    if file.content_length > app.config['MAX_CONTENT_LENGTH']:
        return jsonify({'error': 'File size exceeds 16MB limit'}), 400
    
    # Генерация уникального ID для сообщения
    message_id = str(uuid.uuid4())
    
    # Сохранение файла с оригинальным расширением
    file_extension = os.path.splitext(file.filename)[1]  # Получаем расширение файла
    filename = secure_filename(f"{message_id}{file_extension}")  # Сохраняем с оригинальным расширением
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({'error': 'Failed to save file'}), 500
    
    # Генерация QR-кода
    try:
        qr_path = generate_qr(message_id)
    except Exception as e:
        return jsonify({'error': 'Failed to generate QR code'}), 500
    
    return jsonify({
        'message_id': message_id,
        'qr_url': f"/static/uploads/qr_{message_id}.png",
        'audio_url': f"/get_audio/{message_id}"
    })

@app.route('/get_audio/<message_id>')
def get_audio(message_id):
    # Ищем файл с таким message_id, но с любым расширением
    for file in os.listdir(app.config['UPLOAD_FOLDER']):
        if file.startswith(message_id):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
            return send_file(file_path)
    
    return jsonify({'error': 'File not found'}), 404

@app.route('/listen/<message_id>')
def listen_page(message_id):
    return render_template('listen.html', message_id=message_id)

# @app.route('/get_audio/<message_id>')
# def get_audio(message_id):
#     file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{message_id}.wav")
#     if os.path.exists(file_path):
#         return send_file(file_path)
#     return jsonify({'error': 'File not found'}), 404

if __name__ == "__main__":
    setup_upload_directory()
    app.run(host="0.0.0.0", port=5000)
