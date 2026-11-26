from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/extract', methods=['POST'])
def extract_video():
    data = request.get_json(silent=True) or {}
    video_url = data.get('url', '').strip()
    if not video_url:
        return jsonify({'error': True, 'message': 'No URL provided'}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        medias = []
        formats = info.get('formats', [])
        for f in formats:
            url = f.get('url')
            if not url:
                continue
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            if vcodec == 'none' and acodec == 'none':
                continue

            is_audio = (vcodec == 'none' and acodec != 'none')
            quality = f.get('format_note') or (f"{f.get('height')}p" if f.get('height') else ('audio' if is_audio else 'default'))

            medias.append({
                'url': url,
                'quality': quality,
                'type': 'audio' if is_audio else 'video',
                'extension': f.get('ext', 'mp3' if is_audio else 'mp4'),
                'data_size': f.get('filesize') or f.get('filesize_approx')
            })

        # Fallback if formats list had no valid entries
        if not medias and info.get('url'):
            medias.append({
                'url': info['url'],
                'quality': 'default',
                'type': 'video',
                'extension': info.get('ext', 'mp4'),
                'data_size': info.get('filesize')
            })

        return jsonify({
            'id': info.get('id', ''),
            'title': info.get('title', 'Untitled'),
            'author': info.get('uploader') or info.get('channel') or 'Unknown',
            'source': info.get('extractor_key') or info.get('extractor') or 'social',
            'duration': info.get('duration'),
            'medias': medias
        })
    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
