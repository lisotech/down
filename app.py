import os
import tempfile
import glob
from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)

TEMP_DIR = tempfile.gettempdir()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch-info', methods=['POST'])
def fetch_info():
    data = request.get_json(silent=True)
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400

    url = data.get('url')

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
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
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid request body'}), 400

    url = data.get('url')
    download_type = data.get('type')  # 'mp4' or 'mp3'

    if not url or not download_type:
        return jsonify({'error': 'Invalid parameters'}), 400

    # Clean filename pattern template
    output_template = os.path.join(TEMP_DIR, '%(id)s.%(ext)s')

    if download_type == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'overwrites': True
        }
    else:  # MP4
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'quiet': True,
            'overwrites': True
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get('id')
            title = info.get('title', 'downloaded_media')
            
            # Find the generated file based on video ID
            extension = 'mp3' if download_type == 'mp3' else 'mp4'
            target_file = os.path.join(TEMP_DIR, f"{video_id}.{extension}")

            if not os.path.exists(target_file):
                # Fallback search if extension differed during extraction
                matching_files = glob.glob(os.path.join(TEMP_DIR, f"{video_id}.*"))
                if matching_files:
                    target_file = matching_files[0]
                else:
                    return jsonify({'error': 'File processing failed on server'}), 500

            # Safe download response with proper attachment headers
            safe_filename = f"{title}.{extension}".replace('/', '_').replace('\\', '_')
            return send_file(
                target_file, 
                as_attachment=True, 
                download_name=safe_filename,
                mimetype='audio/mpeg' if download_type == 'mp3' else 'video/mp4'
            )

    except Exception as e:
        return jsonify({'error': f"Download failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
