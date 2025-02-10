/* static/script.js */
let mediaRecorder;
let audioChunks = [];
let timerInterval;
let startTime;

document.getElementById('recordButton').addEventListener('click', toggleRecording);

function toggleRecording() {
    const button = document.getElementById('recordButton');
    
    if (button.textContent === 'Начать запись') {
        startRecording();
        button.textContent = 'Остановить запись';
        button.style.backgroundColor = '#dc3545';
    } else {
        stopRecording();
        button.textContent = 'Начать запись';
        button.style.backgroundColor = '#1a73e8';
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = uploadAudio;
        
        audioChunks = [];
        mediaRecorder.start();
        
        // Запускаем таймер
        startTime = Date.now();
        updateTimer();
        timerInterval = setInterval(updateTimer, 1000);
        
    } catch (err) {
        console.error('Error accessing microphone:', err);
        alert('Ошибка доступа к микрофону. Пожалуйста, проверьте разрешения.');
    }
}

function stopRecording() {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(track => track.stop());
    clearInterval(timerInterval);
}

function updateTimer() {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
    const seconds = (elapsed % 60).toString().padStart(2, '0');
    document.getElementById('timer').textContent = `${minutes}:${seconds}`;
}

document.getElementById('uploadButton').addEventListener('click', handleFileUpload);

function handleFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Пожалуйста, выберите файл');
        return;
    }
    
    const formData = new FormData();
    formData.append('audio', file);
    
    uploadFile(formData);
}

async function uploadFile(formData) {
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('qrCode').src = data.qr_url;
            document.getElementById('downloadQR').href = data.qr_url;
            document.getElementById('result').classList.remove('hidden');
        } else {
            alert('Ошибка при загрузке файла: ' + data.error);
        }
    } catch (err) {
        console.error('Error uploading file:', err);
        alert('Ошибка при загрузке файла');
    }
}

async function uploadAudio() {
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('audio', audioBlob);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('qrCode').src = data.qr_url;
            document.getElementById('downloadQR').href = data.qr_url;
            document.getElementById('result').classList.remove('hidden');
        } else {
            alert('Ошибка при загрузке аудио: ' + data.error);
        }
    } catch (err) {
        console.error('Error uploading audio:', err);
        alert('Ошибка при загрузке аудио');
    }
}