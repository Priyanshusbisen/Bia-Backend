import datetime
import uuid
from enum import Enum
import sqlalchemy as sqlalc
from sqlalchemy.dialects.postgresql import UUID, JSON
from app.extentions import db
from sqlalchemy import String, ARRAY
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy import UniqueConstraint
import logging

class VideoReview(db.Model):
    __tablename__ = 'interview_summary'

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    video_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('interviews.id'), nullable=False)
    candidate_name = db.Column(db.String(255), unique=False, nullable=True)
    body_language = db.Column(db.Float, nullable=True)  
    eye_contact_with_interviewers = db.Column(db.Float, nullable=True)  
    confidence = db.Column(db.Float, nullable=True)  
    vocabulary_and_grammar = db.Column(db.Float, nullable=True)  
    engagement_with_interviewers = db.Column(db.Float, nullable=True)  
    leadership_traits = db.Column(db.Float, nullable=True)  
    candidate_gender = db.Column(db.String(50), nullable=True)  
    candidate_attire = db.Column(db.String(255), nullable=True)  
    native_english_speaker = db.Column(db.String(5), nullable=True)  
    interview_summary = db.Column(db.Text, nullable=True)  
    overall_score = db.Column(db.Float, nullable=True)  
    five_key_attributes = db.Column(db.Text, nullable=True)

class Video(db.Model):
    __tablename__ = 'interviews'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    candidate_name = db.Column(db.String(255), unique=False, nullable=True)
    video_url = db.Column(db.String(512), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)