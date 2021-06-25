#!/usr/bin/env python
# encoding: utf-8
import datetime
import json
from flask import Flask, request, jsonify
from flask_mongoengine import MongoEngine

app = Flask(__name__)
app.config.from_file("../config.json", load=json.load)
db = MongoEngine()
db.init_app(app)


class FeedPost(db.Document):
    meta = {'collection': app.config.get("DB_COLLECTION_NAME_FEED_POST")}
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
    FeedPost.objects.insert(FeedPost(
        userId=request.json['userId'],
        contentReference=request.json['path'],
        timestamp=datetime.datetime.now())
    )
    return {}, 200


if __name__ == "__main__":
    app.run(debug=True)

app.run()
