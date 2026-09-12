import os
import tempfile
from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)

# Directory to temporarily store downloads
TEMP_DIR = tempfile.gettempdir()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch-info', methods=['POST'])
def fetch_info():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Format basic metadata
            response_data = {
                'title': info.get('title', 'Media Content'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration_string', 'N/A'),
                'uploader': info.get('uploader', info.get('extractor_key', 'Unknown')),
                'url': url
            }
            return jsonify(response_data)
            
    except Exception as e:
        return jsonify({'error': f"Failed to process URL: {str(e)}"}), 500

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    download_type = data.get('type') # 'mp4' or 'mp3'

    if not url or not download_type:
        return jsonify({'error': 'Invalid parameters'}), 400

    output_template = os.path.join(TEMP_DIR, '%(title)s.%(ext)s')

    if download_type == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }
    else:  # MP4
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'quiet': True
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Adjust extension for mp3 post-processing
            if download_type == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'

            return send_file(filename, as_attachment=True)

    except Exception as e:
        return jsonify({'error': f"Download failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
