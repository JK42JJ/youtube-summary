from flask import Flask, request, jsonify
import yt_dlp
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({'status': 'YouTube Transcript API is running'})

@app.route('/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get('video_id')
    lang = request.args.get('lang', 'ko')  # 기본값: 한국어
    
    if not video_id:
        return jsonify({'error': 'video_id parameter required'}), 400
    
    url = f'https://www.youtube.com/watch?v={video_id}'
    
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': [lang, 'en'],
        'skip_download': True,
        'quiet': True,
        'no_warnings': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # 자막 찾기
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})
            
            # 요청한 언어 우선, 없으면 영어
            transcript_list = (
                subtitles.get(lang) or 
                automatic_captions.get(lang) or 
                subtitles.get('en') or 
                automatic_captions.get('en')
            )
            
            if not transcript_list:
                return jsonify({'error': 'No subtitles available'}), 404
            
            # JSON3 형식 찾기
            json3_url = None
            for sub in transcript_list:
                if sub.get('ext') == 'json3':
                    json3_url = sub.get('url')
                    break
            
            if not json3_url:
                return jsonify({'error': 'JSON3 format not available'}), 404
            
            # 자막 다운로드
            response = requests.get(json3_url)
            transcript_data = response.json()
            
            # 텍스트만 추출
            text_only = []
            for event in transcript_data.get('events', []):
                if 'segs' in event:
                    for seg in event['segs']:
                        if 'utf8' in seg:
                            text_only.append(seg['utf8'])
            
            return jsonify({
                'video_id': video_id,
                'language': lang,
                'transcript': ' '.join(text_only),
                'full_data': transcript_data
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
