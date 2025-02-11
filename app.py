from flask import Flask, render_template, request, jsonify, send_file
import os
import qrcode
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp'  # Временная папка для хранения файлов

def generate_qr(message_id):
    """Генерирует QR-код для сообщения"""
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
    if file.content_length and file.content_length > app.config['MAX_CONTENT_LENGTH']:
        return jsonify({'error': 'File size exceeds 16MB limit'}), 400
    
    # Генерация уникального ID для сообщения
    message_id = str(uuid.uuid4())
    
    # Сохранение файла с оригинальным расширением в /tmp/
    file_extension = os.path.splitext(file.filename)[1]  
    filename = secure_filename(f"{message_id}{file_extension}")  
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({'error': f'Failed to save file: {str(e)}'}), 500
    
    # Генерация QR-кода
    try:
        qr_path = generate_qr(message_id)
    except Exception as e:
        return jsonify({'error': f'Failed to generate QR code: {str(e)}'}), 500
    
    return jsonify({
        'message_id': message_id,
        'qr_url': f"/get_qr/{message_id}",
        'audio_url': f"/get_audio/{message_id}"
    })

@app.route('/get_audio/<message_id>')
def get_audio(message_id):
    """Возвращает загруженный аудиофайл"""
    for file in os.listdir(app.config['UPLOAD_FOLDER']):
        if file.startswith(message_id):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
            return send_file(file_path, as_attachment=True)
    
    return jsonify({'error': 'File not found'}), 404

@app.route('/get_qr/<message_id>')
def get_qr(message_id):
    """Возвращает QR-код по message_id"""
    qr_path = os.path.join(app.config['UPLOAD_FOLDER'], f'qr_{message_id}.png')
    if os.path.exists(qr_path):
        return send_file(qr_path, mimetype='image/png')
    
    return jsonify({'error': 'QR code not found'}), 404

@app.route('/listen/<message_id>')
def listen_page(message_id):
    """Рендерит страницу для прослушивания"""
    return render_template('listen.html', message_id=message_id)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
