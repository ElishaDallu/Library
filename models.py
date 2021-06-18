# pip install Flask-SQLAlchemy # version 2.5.1
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bookID = db.Column(db.Integer(), nullable=True)
    title = db.Column(db.String(), nullable=True)
    authors = db.Column(db.String(), nullable=True)
    average_rating = db.Column(db.Integer(), nullable=True)
    isbn = db.Column(db.Integer(), nullable=True)
    isbn13 = db.Column(db.Integer(), nullable=True)
    language_code = db.Column(db.String(), nullable=True)
    num_pages = db.Column(db.Integer(), nullable=True)
    ratings_count = db.Column(db.Integer(), nullable=True)
    text_reviews_count = db.Column(db.Integer(), nullable=True)
    publication_date = db.Column(db.String(), nullable=True)
    publisher = db.Column(db.String(), nullable=True)
    total_quantity = db.Column(db.Integer(), nullable=True)
    available_quantity = db.Column(db.Integer(), nullable=True)
    date_created = db.Column(db.DateTime(), default=datetime.utcnow)
    date_updated = db.Column(db.DateTime(), default=datetime.utcnow)
    is_valid = db.Column(db.Boolean(), default=True)
    reason = db.Column(db.String(), nullable=True)
    transaction = db.relationship("Transaction")


class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_fname = db.Column(db.String(), nullable=False)
    member_lname = db.Column(db.String(), nullable=False)
    member_address = db.Column(db.String(100))
    date_created = db.Column(db.DateTime(), default=datetime.utcnow)
    date_updated = db.Column(db.DateTime(), default=datetime.utcnow)
    transaction = db.relationship("Transaction")


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer(), db.ForeignKey('book.id'))
    member_id = db.Column(db.Integer(), db.ForeignKey('member.id'))
    status = db.Column(db.String(), nullable=False)
    issued_for_days = db.Column(db.Integer(), nullable=True)
    issue_date = db.Column(db.DateTime(), default=datetime.utcnow)
    return_date = db.Column(db.DateTime(), nullable=True)
    rent = db.Column(db.Float(), nullable=True)
