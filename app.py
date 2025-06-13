from flask import Flask, request, jsonify
import os
import whisper
from werkzeug.utils import secure_filename
from googletrans import Translator

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load Whisper model
model = whisper.load_model("base")
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
        result = model.transcribe(filepath)
        original_text = result['text']

        target_lang = request.args.get('target_lang')  # e.g. ?target_lang=ar
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
    app.run(debug=True, port=5000)
