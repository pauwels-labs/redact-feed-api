#!/usr/bin/env python
# encoding: utf-8
import datetime
import json
from flask import Flask, request, jsonify
from flask_mongoengine import MongoEngine
import os

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'db': os.getenv('MONGODB_DB'),
    'host': os.getenv('MONGODB_HOST'),
    'port': int(os.getenv('MONGODB_PORT'))
}
db = MongoEngine()
db.init_app(app)


class FeedPost(db.Document):
    meta = {'collection': os.getenv('DB_COLLECTION_NAME_FEED_POST')}
    userId = db.StringField()
    contentReference = db.StringField()
    timestamp = db.DateTimeField()


@app.route("/feed/<user_id>", methods=['GET'])
def index(user_id):
    entries = FeedPost.objects(userId=user_id).order_by('-timestamp')
    response_entries = []
    for entry in entries:
        response_entries.append({
            "userId": entry.userId,
            "contentReference": entry.contentReference,
            "createdOn": entry.timestamp.isoformat()
        })
    return jsonify(response_entries), 200


@app.route("/redact/relay", methods=['POST'])
def redact_relay():
    cert = request.headers.get("ssl-client-cert")

    FeedPost.objects.insert(FeedPost(
        userId=request.json['userId'],
        contentReference=request.json['path'],
        timestamp=datetime.datetime.now())
    )
    return {cert: cert}, 200


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port='8080')

app.run(host='0.0.0.0', port='8080')
