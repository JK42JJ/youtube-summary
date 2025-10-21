from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({'status': 'YouTube Transcript API is running'})

@app.route('/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get('video_id')
    lang = request.args.get('lang', 'ko')
    
    if not video_id:
        return jsonify({'error': 'video_id parameter required'}), 400
    
    # YouTube 자막 API 직접 호출
    url = f'https://www.youtube.com/api/timedtext?lang={lang}&v={video_id}&fmt=json3'
    
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code != 200:
            # 한국어 자막이 없으면 영어 시도
            url = f'https://www.youtube.com/api/timedtext?lang=en&v={video_id}&fmt=json3'
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
        
        if response.status_code != 200:
            return jsonify({'error': 'No subtitles available'}), 404
        
        data = response.json()
        
        # 텍스트 추출
        text_only = []
        for event in data.get('events', []):
            if 'segs' in event:
                for seg in event['segs']:
                    if 'utf8' in seg:
                        text_only.append(seg['utf8'])
        
        return jsonify({
            'video_id': video_id,
            'language': lang,
            'transcript': ' '.join(text_only),
            'full_data': data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)