from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

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
    
    try:
        # 자막 가져오기
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # 원하는 언어 찾기
        try:
            transcript = transcript_list.find_transcript([lang])
        except NoTranscriptFound:
            # 한국어 없으면 영어 시도
            try:
                transcript = transcript_list.find_transcript(['en'])
                lang = 'en'
            except NoTranscriptFound:
                return jsonify({
                    'error': 'No transcript found in requested language',
                    'video_id': video_id
                }), 404
        
        # 자막 텍스트 가져오기
        transcript_data = transcript.fetch()
        
        # 텍스트만 추출
        text_only = ' '.join([item['text'] for item in transcript_data])
        
        return jsonify({
            'video_id': video_id,
            'language': lang,
            'transcript': text_only,
            'text_length': len(text_only),
            'segment_count': len(transcript_data)
        })
        
    except TranscriptsDisabled:
        return jsonify({
            'error': 'Transcripts are disabled for this video',
            'video_id': video_id
        }), 404
    except VideoUnavailable:
        return jsonify({
            'error': 'Video is unavailable',
            'video_id': video_id
        }), 404
    except Exception as e:
        return jsonify({
            'error': str(e),
            'video_id': video_id,
            'error_type': type(e).__name__
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)