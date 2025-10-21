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
        response = requests.get(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
            timeout=30
        )
        
        # 응답 상태 확인
        if response.status_code != 200:
            # 한국어 자막이 없으면 영어 시도
            url_en = f'https://www.youtube.com/api/timedtext?lang=en&v={video_id}&fmt=json3'
            response = requests.get(
                url_en, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                timeout=30
            )
            lang = 'en'
        
        if response.status_code != 200:
            return jsonify({
                'error': 'No subtitles available',
                'video_id': video_id,
                'status_code': response.status_code
            }), 404
        
        # 응답이 비어있는지 확인
        if not response.text or len(response.text.strip()) == 0:
            return jsonify({
                'error': 'Empty response from YouTube',
                'video_id': video_id
            }), 404
        
        # JSON 파싱 시도
        try:
            data = response.json()
        except ValueError as e:
            return jsonify({
                'error': 'Invalid JSON response',
                'video_id': video_id,
                'response_preview': response.text[:200]
            }), 500
        
        # 텍스트 추출
        text_only = []
        events = data.get('events', [])
        
        if not events:
            return jsonify({
                'error': 'No transcript events found',
                'video_id': video_id
            }), 404
        
        for event in events:
            if 'segs' in event:
                for seg in event['segs']:
                    if 'utf8' in seg:
                        text_only.append(seg['utf8'])
        
        transcript_text = ' '.join(text_only)
        
        if not transcript_text:
            return jsonify({
                'error': 'No text in transcript',
                'video_id': video_id
            }), 404
        
        return jsonify({
            'video_id': video_id,
            'language': lang,
            'transcript': transcript_text,
            'text_length': len(transcript_text),
            'event_count': len(events)
        })
        
    except requests.Timeout:
        return jsonify({'error': 'Request timeout', 'video_id': video_id}), 504
    except Exception as e:
        return jsonify({
            'error': str(e),
            'video_id': video_id,
            'error_type': type(e).__name__
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)