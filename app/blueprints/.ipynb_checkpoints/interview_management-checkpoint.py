from flask.views import MethodView
from flask import request, jsonify
from app.utils.interview_analysis import analyze_video, upload_to_gcp, list_objects
from app.models import VideoReview, Video
from app.extentions import db
import logging
import json
from sqlalchemy.orm.exc import NoResultFound
import os

class ZoomRecordings(MethodView):
    def get(self, video_id=None):
        try:
            if video_id:
                video_data = db.session.query(Video).filter(Video.id == video_id).one_or_none()

                if video_data:
                    return jsonify({
                        "message": "Video info successfully fetched",
                        "video": {
                            "video_id": str(video_data.id),
                            "candidate_name": video_data.candidate_name,
                            "gcp_url": video_data.video_url
                        }
                    }), 200
                else:
                    return jsonify({"message": "Video data not found"}), 404
            else:
                videos = db.session.query(Video).all()

                video_list = [
                    {
                        "video_id": str(video.id),
                        "candidate_name": video.candidate_name,
                        "gcp_url": video.video_url
                    } for video in videos
                ]

                return jsonify({
                    "message": "All videos fetched successfully",
                    "videos": video_list
                }), 200

        except Exception as e:
            logging.error(f"Error in fetching video data: {e}")
            return jsonify({"message": f"Error in fetching video data: {e}"}), 500

    def post(self):
        try:
            UPLOAD_FOLDER = 'recordings'
        
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            
            if 'interviews' not in request.files:
                return jsonify({"error": "No file part in the request."}), 400

            file = request.files['interviews']
            logging.info(request)
            if file.filename == '':
                return jsonify({"error": "No selected file."}), 400

            if not file.filename.lower().endswith(('mp4', 'avi', 'mov', 'mkv')):
                return jsonify({"error": "Invalid file format. Allowed: mp4, avi, mov, mkv."}), 400
            candidate_name = file.filename.lower().split(',')[0]
            save_path = os.path.join(os.getcwd(), UPLOAD_FOLDER, file.filename)
            file.save(save_path)

            gcp_url = upload_to_gcp(save_path)

            if gcp_url:
                video = Video(
                    candidate_name=candidate_name,
                    video_url=gcp_url
                )

                db.session.add(video)
                db.session.commit()

                return jsonify({
                    "message": "File uploaded successfully.",
                    "file_path": save_path,
                    "gcp_url": gcp_url
                }), 200

            return jsonify({"error": "Failed to upload to GCP."}), 500

        except Exception as e:
            logging.error(f"Error in uploading video: {e}")
            return jsonify({"error": str(e)}), 500


class AnalyseRecordings(MethodView):
    def post(self, video_id=None):
        if not video_id:
            try:
                videos = db.session.query(Video.id, Video.candidate_name, Video.video_url).all()

                for video_id, candidate_name, gcp_url in videos:
                    soft_skill_review = analyze_video(gcp_url)

                    if soft_skill_review:
                        video_review = VideoReview(
                            video_id=video_id,
                            candidate_name=candidate_name,
                            body_language=soft_skill_review.get("body_language"),
                            eye_contact_with_interviewers=soft_skill_review.get("eye_contact_with_interviewers"),
                            confidence=soft_skill_review.get("confidence"),
                            vocabulary_and_grammar=soft_skill_review.get("vocabulary_and_grammar"),
                            engagement_with_interviewers=soft_skill_review.get("engagement_with_interviewers"),
                            leadership_traits=soft_skill_review.get("leadership_traits"),
                            candidate_gender=soft_skill_review.get("candidate_gender"),
                            candidate_attire=soft_skill_review.get("candidate_attire"),
                            native_english_speaker=soft_skill_review.get("native_english_speaker").strip(),
                            interview_summary=soft_skill_review.get("interview_summary"),
                            overall_score=soft_skill_review.get("overall_score"),
                            five_key_attributes=soft_skill_review.get("five_key_attributes")
                        )

                        db.session.add(video_review)
                        db.session.commit()

                        logging.info(f"Zoom interview summary added successfully with id {video_review.id}")

                return jsonify({"message": "Interview Summaries Successfully added"}), 200

            except Exception as e:
                logging.error(f"Error in processing recordings: {e}")
                return jsonify({"error": f"An error occurred: {e}"}), 500
        else:
            try:
                video = db.session.query(Video).filter(Video.id == video_id).first()
                logging.info(video)
                if not video:
                    return jsonify({"message": "Video not found"}), 404

                soft_skill_review = analyze_video(video.video_url)
                logging.info(soft_skill_review)
                if soft_skill_review:
                    video_review = VideoReview(
                        video_id=video.id,
                        candidate_name=video.candidate_name,
                        body_language=soft_skill_review.get("body_language"),
                        eye_contact_with_interviewers=soft_skill_review.get("eye_contact_with_interviewers"),
                        confidence=soft_skill_review.get("confidence"),
                        vocabulary_and_grammar=soft_skill_review.get("vocabulary_and_grammar"),
                        engagement_with_interviewers=soft_skill_review.get("engagement_with_interviewers"),
                        leadership_traits=soft_skill_review.get("leadership_traits"),
                        candidate_gender=soft_skill_review.get("candidate_gender"),
                        candidate_attire=soft_skill_review.get("candidate_attire"),
                        native_english_speaker=soft_skill_review.get("native_english_speaker"),
                        interview_summary=soft_skill_review.get("interview_summary"),
                        overall_score=soft_skill_review.get("overall_score"),
                        five_key_attributes=soft_skill_review.get("five_key_attributes")
                    )

                    db.session.add(video_review)
                    db.session.commit()

                    logging.info(f"interview summary added successfully with id {video_review.id}")

                return jsonify({"message": "Interview Summary Successfully added"}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({"message": f"Error in uploading interview: {e}"}), 500
                
    def get(self, video_id=None):
        try:
            if video_id:
                video = db.session.query(Video).filter(Video.id == video_id).first()
                
                if not video:
                    return jsonify({"message": "Video not found"}), 404

                video_review = db.session.query(VideoReview).filter(VideoReview.video_id == video_id).first()
                
                if not video_review:
                    return jsonify({"message": "No review found for the given video"}), 404

                return jsonify({
                    "video_id": video.id,
                    "candidate_name": video.candidate_name,
                    "video_url": video.video_url,
                    "review": {
                        "body_language": video_review.body_language,
                        "eye_contact_with_interviewers": video_review.eye_contact_with_interviewers,
                        "confidence": video_review.confidence,
                        "vocabulary_and_grammar": video_review.vocabulary_and_grammar,
                        "engagement_with_interviewers": video_review.engagement_with_interviewers,
                        "leadership_traits": video_review.leadership_traits,
                        "candidate_gender": video_review.candidate_gender,
                        "candidate_attire": video_review.candidate_attire,
                        "native_english_speaker": video_review.native_english_speaker,
                        "interview_summary": video_review.interview_summary,
                        "overall_score": video_review.overall_score,
                        "five_key_attributes": video_review.five_key_attributes
                    }
                }), 200
            else:
                videos = db.session.query(Video).all()

                result = []
                for video in videos:
                    video_review = db.session.query(VideoReview).filter(VideoReview.video_id == video.id).one_or_none()

                    result.append({
                        "video_id": video.id,
                        "candidate_name": video.candidate_name,
                        "video_url": video.video_url,
                        "review": {
                            "body_language": video_review.body_language if video_review else None,
                            "eye_contact_with_interviewers": video_review.eye_contact_with_interviewers if video_review else None,
                            "confidence": video_review.confidence if video_review else None,
                            "vocabulary_and_grammar": video_review.vocabulary_and_grammar if video_review else None,
                            "engagement_with_interviewers": video_review.engagement_with_interviewers if video_review else None,
                            "leadership_traits": video_review.leadership_traits if video_review else None,
                            "candidate_gender": video_review.candidate_gender if video_review else None,
                            "candidate_attire": video_review.candidate_attire if video_review else None,
                            "native_english_speaker": video_review.native_english_speaker if video_review else None,
                            "interview_summary": video_review.interview_summary if video_review else None,
                            "overall_score": video_review.overall_score if video_review else None,
                            "five_key_attributes": video_review.five_key_attributes if video_review else None
                        }
                    })

                return jsonify(result), 200

        except Exception as e:
            logging.error(f"Error in fetching videos or reviews: {e}")
            return jsonify({"message": f"Error in fetching videos or reviews: {e}"}), 500
        
        


        
                
            
                
            