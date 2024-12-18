from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import json
from datetime import datetime
import vertexai
import requests
import base64
import os
import google.cloud.storage as gcs
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

vertexai.init(project="interview-analysis-444315", location="us-east1")
model = GenerativeModel("gemini-1.5-flash-001")

GCS_BUCKET_NAME = "bia-810"
GCS_VIDEO_PATH = "recordings"

def analyze_video(video_url):
    try:
        logger.info(f"Started analyzing video from URL: {video_url}")
        prompt = """
        This is a video of an interview wherein a candidate is being interviewed as a potential hire.
        Please analyze the visuals and audio and assign a score to the candidate against the following 6 metrics:
        1. Body language
        2. Eye contact with interviewers
        3. Confidence
        4. Vocabulary and grammar
        5. Engagement with the interviewers
        6. Leadership traits

        The score for these metrics should be a number between 1-5, with 5 being the best in class.

        Additionally, provide the following 3 pieces of information:
        1. Gender of the candidate (male or female)
        2. Description of the candidate's attire
        3. Whether the candidate is a native English speaker or not (yes or no)

        Finally, provide a summary of the entire interview, in less than 10 sentences.

        Please provide the entire response in JSON format only, using this structure:
        {
            "body_language": <score>,
            "eye_contact_with_interviewers": <score>,
            "confidence": <score>,
            "vocabulary_and_grammar": <score>,
            "engagement_with_interviewers": <score>,
            "leadership_traits": <score>,
            "candidate_gender": <gender>,
            "candidate_attire": <attire>,
            "native_english_speaker": <yes/no>,
            "interview_summary": <summary>,
            "overall_score":<score>,
            "five_key_attributes":<attributes>
        }
        """

        video_file = Part.from_uri(uri=video_url, mime_type="video/mp4")
        generation_config = GenerationConfig(temperature=0)
        contents = [video_file, prompt]

        logger.info("Requesting model to generate content")
        response = model.generate_content(contents, generation_config=generation_config)
        parsed_response = json.loads(response.candidates[0].content.parts[0].text)
        logger.info("Successfully parsed model response")
        
        return parsed_response

    except Exception as e:
        logger.error(f"Error in analyzing video: {str(e)}")
        return jsonify({"error": str(e)}), 500

def upload_to_gcp(local_file):
    """ Upload the downloaded video to Google Cloud Storage and return the GCS URL. """
    try:
        logger.info(f"Uploading video {local_file} to Google Cloud Storage")
        storage_client = gcs.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)

        
        destination_blob_name = GCS_VIDEO_PATH +'/'+ os.path.basename(local_file)
        blob = bucket.blob(destination_blob_name)

        
        blob.upload_from_filename(local_file)
        gcs_url = blob.public_url

        logger.info(f"Successfully uploaded to GCS, URL: {gcs_url}")
        return gcs_url
    except Exception as e:
        logger.error(f"Error in uploading video to GCP: {str(e)}")
        return None

def list_objects():
    try:
        storage_client = gcs.Client()

        prefix = GCS_VIDEO_PATH + '/'
        
        blobs = storage_client.list_blobs(GCS_BUCKET_NAME, prefix=prefix, delimiter='/')
        output = {}
        for blob in blobs:
            output[blob.name] = blob.public_url
        logging.info(f'Blobs fetched')
        return output
    except Exception as e:
        logging.error(f'Error in fetching Blobs: {e}')
            






        