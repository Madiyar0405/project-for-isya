from flask import Flask, render_template, request, jsonify, send_file
import os
import qrcode
from werkzeug.utils import secure_filename
import uuid
import logging
from pathlib import Path

app = Flask(__name__)

# Абсолютный путь к директории проекта
BASE_DIR = Path(__file__).resolve().parent

# Конфигурация с абсолютными путями
app.config.update(
    UPLOAD_FOLDER=os.path.join(BASE_DIR, 'static', 'uploads'),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max file size
    ALLOWED_EXTENSIONS={'wav', 'mp3', 'ogg', 'm4a'}
)

# Настройка логирования для отладки
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.path.join(BASE_DIR, 'app.log')
)
logger = logging.getLogger(__name__)

def setup_upload_directory():
    """Создание директории для загрузок с нужными правами"""
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        # Установка прав доступа 755 для директории
        os.chmod(app.config['UPLOAD_FOLDER'], 0o755)
        logger.info(f"Upload directory created/verified: {app.config['UPLOAD_FOLDER']}")
    except Exception as e:
        logger.error(f"Failed to create upload directory: {str(e)}")
        raise

def generate_qr(message_id):
    """Генерирует QR код с обработкой ошибок и логированием"""
    try:
        # Создаем QR код
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        
        # Используем полный URL для QR кода
        full_url = f"{request.host_url.rstrip('/')}/listen/{message_id}"
        logger.debug(f"Generating QR code for URL: {full_url}")
        
        qr.add_data(full_url)
        qr.make(fit=True)
        
        # Создаем изображение
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Формируем путь для сохранения
        qr_filename = f'qr_{message_id}.png'
        qr_path = os.path.join(app.config['UPLOAD_FOLDER'], qr_filename)
        
        # Сохраняем изображение
        img.save(qr_path)
        logger.info(f"QR code generated successfully: {qr_path}")
        
        # Проверяем, что файл действительно создан
        if not os.path.exists(qr_path):
            raise Exception("QR code file was not created")
            
        # Устанавливаем права доступа для файла
        os.chmod(qr_path, 0o644)
        
        return qr_path
        
    except Exception as e:
        logger.error(f"QR generation failed: {str(e)}")
        raise

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['audio']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Генерация ID и сохранение файла
        message_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        filename = secure_filename(f"{message_id}{file_extension}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Сохраняем аудио файл
        file.save(file_path)
        os.chmod(file_path, 0o644)  # Устанавливаем права доступа
        
        # Генерируем QR код
        qr_path = generate_qr(message_id)
        
        return jsonify({
            'message_id': message_id,
            'qr_url': f"/static/uploads/qr_{message_id}.png",
            'audio_url': f"/get_audio/{message_id}"
        })
        
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        return jsonify({'error': f'Failed to process upload: {str(e)}'}), 500

if __name__ == "__main__":
    setup_upload_directory()
    app.run(host="0.0.0.0", port=5000)
