from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
from googletrans import Translator
from faster_whisper import WhisperModel  # NEW import

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load Faster-Whisper model (base or tiny)
model = WhisperModel("base", compute_type="int8")  # optimized for CPU
translator = Translator()

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        segments, _ = model.transcribe(filepath)
        original_text = " ".join(segment.text for segment in segments)

        target_lang = request.args.get('target_lang')
        if target_lang:
            translated = translator.translate(original_text, dest=target_lang)
            return jsonify({
                'text': original_text,
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
