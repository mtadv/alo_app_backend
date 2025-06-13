from flask import Flask, request, jsonify
import os
import requests
from werkzeug.utils import secure_filename
from googletrans import Translator
import time

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# AssemblyAI API
ASSEMBLYAI_API_KEY = '0da22ba07b2a4a46a5c4ae4ac09ba292'
ASSEMBLYAI_HEADERS = {
    'authorization': ASSEMBLYAI_API_KEY,
    'content-type': 'application/json'
}

# Google Translate
translator = Translator()

# Upload audio file to AssemblyAI
def upload_to_assemblyai(file_path):
    with open(file_path, 'rb') as f:
        response = requests.post(
            'https://api.assemblyai.com/v2/upload',
            headers={'authorization': ASSEMBLYAI_API_KEY},
            files={'file': f}
        )
    response.raise_for_status()
    return response.json()['upload_url']

# Start transcription request
def request_transcription(audio_url):
    json_data = {
        "audio_url": audio_url,
        "language_code": "en"  # Or auto-detect: remove this line
    }
    response = requests.post(
        'https://api.assemblyai.com/v2/transcript',
        headers=ASSEMBLYAI_HEADERS,
        json=json_data
    )
    response.raise_for_status()
    return response.json()['id']

# Poll until transcription is ready
def poll_transcription(transcript_id):
    polling_url = f'https://api.assemblyai.com/v2/transcript/{transcript_id}'
    while True:
        response = requests.get(polling_url, headers=ASSEMBLYAI_HEADERS)
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'completed':
            return data['text']
        elif data['status'] == 'error':
            raise Exception(data['error'])
        time.sleep(3)  # wait before next poll

@app.route('/transcribe', methods=['POST'])
def transcribe_and_translate():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        # Upload & transcribe
        audio_url = upload_to_assemblyai(filepath)
        transcript_id = request_transcription(audio_url)
        original_text = poll_transcription(transcript_id)

        # Optional translation
        target_lang = request.args.get('target_lang')  # e.g. ?target_lang=ar
        if target_lang:
            translated = translator.translate(original_text, dest=target_lang)
            return jsonify({
                'original_text': original_text,
                'translated_text': translated.text,
                'translated_language': target_lang
            }), 200
        else:
            return jsonify({'text': original_text}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        os.remove(filepath)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
