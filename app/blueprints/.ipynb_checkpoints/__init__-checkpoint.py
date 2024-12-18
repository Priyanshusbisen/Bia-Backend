from flask import Blueprint

api_bp = Blueprint('api', __name__)

from .interview_management import ZoomRecordings, AnalyseRecordings

api_bp.add_url_rule('/video/', view_func=ZoomRecordings.as_view('videos'))
api_bp.add_url_rule('/video/<uuid:video_id>', view_func=ZoomRecordings.as_view('video'))

api_bp.add_url_rule('/analyze-video/<uuid:video_id>', view_func=AnalyseRecordings.as_view('analyze_video'))
api_bp.add_url_rule('/analyze-videos', view_func=AnalyseRecordings.as_view('analyze_videos'))