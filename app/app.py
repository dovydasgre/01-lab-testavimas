from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime

app = Flask(__name__)

app.config["MONGO_URI"] = "mongodb://mongodb:27017/mydatabase"
mongo = PyMongo(app)

# Helper function to validate ObjectId
def validate_object_id(id_str):
    try:
        return ObjectId(id_str)
    except InvalidId:
        return None

# Helper function to fetch user by ID
def get_user(user_id):
    user = mongo.db.users.find_one({"_id": user_id})
    if not user:
        return None, {"error": "User not found"}, 404
    return user, None, 200

# Create a user profile
@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    if not all(key in data for key in ('firstName', 'lastName', 'birthDate', 'bio')):
        return jsonify({"error": "Missing fields"}), 400

    user = {
        "firstName": data['firstName'],
        "lastName": data['lastName'],
        "birthDate": data['birthDate'],
        "bio": data['bio'],
        "following": []
    }
    result = mongo.db.users.insert_one(user)
    return jsonify({"message": "User created", "userId": str(result.inserted_id)}), 201

# Create a post
@app.route('/posts', methods=['POST'])
def create_post():
    data = request.json
    if not all(key in data for key in ('authorId', 'content')):
        return jsonify({"error": "Missing fields"}), 400

    author_id = validate_object_id(data['authorId'])
    if not author_id:
        return jsonify({"error": "Invalid authorId"}), 400

    post = {
        "author": author_id,
        "content": data['content'],
        "createdAt": datetime.utcnow(),
        "likes": [],
        "comments": []
    }
    result = mongo.db.posts.insert_one(post)
    return jsonify({"message": "Post created", "postId": str(result.inserted_id)}), 201

# Add a comment to a post
@app.route('/posts/<post_id>/comments', methods=['POST'])
def add_comment(post_id):
    post_id = validate_object_id(post_id)
    if not post_id:
        return jsonify({"error": "Invalid postId"}), 400

    data = request.json
    if not all(key in data for key in ('authorId', 'text')):
        return jsonify({"error": "Missing fields"}), 400

    author_id = validate_object_id(data['authorId'])
    if not author_id:
        return jsonify({"error": "Invalid authorId"}), 400

    if len(data['text']) > 500:
        return jsonify({"error": "Comment too long"}), 400

    comment = {
        "author": author_id,
        "text": data['text'],
        "createdAt": datetime.utcnow()
    }
    result = mongo.db.posts.update_one(
        {"_id": post_id},
        {"$push": {"comments": comment}}
    )
    if result.matched_count == 0:
        return jsonify({"error": "Post not found"}), 404
    return jsonify({"message": "Comment added"}), 200

# Add a like to a post
@app.route('/posts/<post_id>/likes', methods=['POST'])
def add_like(post_id):
    post_id = validate_object_id(post_id)
    if not post_id:
        return jsonify({"error": "Invalid postId"}), 400

    data = request.json
    if 'userId' not in data:
        return jsonify({"error": "Missing userId"}), 400

    user_id = validate_object_id(data['userId'])
    if not user_id:
        return jsonify({"error": "Invalid userId"}), 400

    post = mongo.db.posts.find_one({"_id": post_id})
    if not post:
        return jsonify({"error": "Post not found"}), 404

    if user_id in post.get('likes', []):
        return jsonify({"error": "User already liked this post"}), 400

    mongo.db.posts.update_one(
        {"_id": post_id},
        {"$push": {"likes": user_id}}
    )
    return jsonify({"message": "Like added"}), 200

# Follow a user
@app.route('/users/<user_id>/follow', methods=['POST'])
def follow_user(user_id):
    user_id = validate_object_id(user_id)
    if not user_id:
        return jsonify({"error": "Invalid userId"}), 400

    data = request.json
    follow_id = validate_object_id(data.get('followId'))
    if not follow_id:
        return jsonify({"error": "Invalid followId"}), 400

    user, error, status = get_user(user_id)
    if error:
        return jsonify(error), status

    if follow_id in user.get('following', []):
        return jsonify({"message": "Already following this user"}), 400

    mongo.db.users.update_one(
        {"_id": user_id},
        {"$push": {"following": follow_id}}
    )
    return jsonify({"message": "Now following the user"}), 200

# Unfollow a user
@app.route('/users/<user_id>/unfollow', methods=['POST'])
def unfollow_user(user_id):
    user_id = validate_object_id(user_id)
    if not user_id:
        return jsonify({"error": "Invalid userId"}), 400

    data = request.json
    unfollow_id = validate_object_id(data.get('unfollowId'))
    if not unfollow_id:
        return jsonify({"error": "Invalid unfollowId"}), 400

    user, error, status = get_user(user_id)
    if error:
        return jsonify(error), status

    if unfollow_id not in user.get('following', []):
        return jsonify({"message": "Not following this user"}), 400

    mongo.db.users.update_one(
        {"_id": user_id},
        {"$pull": {"following": unfollow_id}}
    )
    return jsonify({"message": "Unfollowed the user"}), 200

# Get likes for a post
@app.route('/posts/<post_id>/likes', methods=['GET'])
def get_post_likes(post_id):
    post_id = validate_object_id(post_id)
    if not post_id:
        return jsonify({"error": "Invalid postId"}), 400

    post = mongo.db.posts.find_one({"_id": post_id})
    if not post:
        return jsonify({"error": "Post not found"}), 404

    likes = post.get('likes', [])
    users = []
    for user_id in likes:
        user, error, status = get_user(user_id)
        if user:
            users.append({
                "userId": str(user["_id"]),
                "firstName": user["firstName"],
                "lastName": user["lastName"]
            })
    return jsonify(users), 200

# Get all comments for a post
@app.route('/posts/<post_id>/comments', methods=['GET'])
def get_posts_comments(post_id):
    try:
        # Validate the post ID
        post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
        if not post:
            return jsonify({"error": "Post not found"}), 404

        # Retrieve comments
        comments = post.get("comments", [])
        comments_with_details = []

        for comment in comments:
            author = mongo.db.users.find_one({"_id": comment["author"]})
            if author:
                comments_with_details.append({
                    "text": comment["text"],
                    "createdAt": comment["createdAt"],
                    "authorFirstName": author["firstName"],
                    "authorLastName": author["lastName"]
                })

        return jsonify(comments_with_details), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/users/<user_id>/feed', methods=['GET'])
def get_feed(user_id):
    user_id = validate_object_id(user_id)
    if not user_id:
        return jsonify({"error": "Invalid userId"}), 400

    user, error, status = get_user(user_id)
    if error:
        return jsonify(error), status

    following = user.get('following', [])
    if not following:
        return jsonify([])  # No following, return an empty feed

    page = int(request.args.get('page', 1))
    limit = 20
    skip = (page - 1) * limit

    pipeline = [
        {"$match": {"author": {"$in": following}}},
        {"$sort": {"createdAt": -1}},
        {"$skip": skip},
        {"$limit": limit},
        {"$lookup": {
            "from": "users",
            "localField": "author",
            "foreignField": "_id",
            "as": "authorDetails"
        }},
        {"$project": {
            "content": 1,
            "createdAt": 1,
            "likes": {"$size": "$likes"},
            "comments": {
                "$map": {
                    "input": "$comments",
                    "as": "comment",
                    "in": {
                        "text": "$$comment.text",
                        "author": {"$toString": "$$comment.author"},  # Convert ObjectId to string
                        "createdAt": "$$comment.createdAt"
                    }
                }
            },
            "authorDetails.firstName": 1,
            "authorDetails.lastName": 1
        }}
    ]

    posts = list(mongo.db.posts.aggregate(pipeline))
    for post in posts:
        # Convert ObjectId fields to strings for JSON serialization
        post["_id"] = str(post["_id"])
        post["createdAt"] = post["createdAt"].isoformat()  # Convert datetime to ISO format
        if "authorDetails" in post and post["authorDetails"]:
            author = post["authorDetails"][0]
            post["authorFirstName"] = author["firstName"]
            post["authorLastName"] = author["lastName"]
            del post["authorDetails"]

    return jsonify(posts), 200

# Cleanup function to clear database collections
@app.route('/cleanup', methods=['POST'])
def cleanup_database():
    try:
        # Delete all documents from the 'users' and 'posts' collections
        mongo.db.users.delete_many({})
        mongo.db.posts.delete_many({})
        
        # Log a message for confirmation and send a JSON response
        return jsonify({"status": "success", "message": "Database cleanup successful. Collections cleared."}), 200
    except Exception as e:
        # Handle any errors during cleanup and return error response
        return jsonify({"status": "error", "message": f"Error during database cleanup: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
