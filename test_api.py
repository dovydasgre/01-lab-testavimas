import unittest
import json
import requests
from bson.objectid import ObjectId

BASE_URL = "http://127.0.0.1:5000"

class NoSQLAppLiveTestCase(unittest.TestCase):
    def setUp(self):
        response = requests.post(f"{BASE_URL}/cleanup")
        self.assertEqual(response.status_code, 200)

    def create_user(self, firstName="Jonas", lastName="Petraitis", birthDate="1990-01-01", bio="Test bio"):
        data = {
            "firstName": firstName,
            "lastName": lastName,
            "birthDate": birthDate,
            "bio": bio
        }
        response = requests.post(f"{BASE_URL}/users", json=data)
        return response.json()

    def create_post(self, authorId, content="Test post content"):
        data = {
            "authorId": authorId,
            "content": content
        }
        response = requests.post(f"{BASE_URL}/posts", json=data)
        return response.json()

    def test_create_user_missing_fields(self):
        data = {"firstName": "Jonas", "lastName": "Petraitis"}
        response = requests.post(f"{BASE_URL}/users", json=data)
        self.assertEqual(response.status_code, 400)
        res = response.json()
        self.assertIn("error", res)

    def test_create_user_success(self):
        res = self.create_user("Algis", "Kazlauskas", "1985-05-15", "Bio")
        self.assertEqual(res["message"], "User created")
        self.assertIn("userId", res)

    def test_create_post_missing_fields(self):
        data = {"authorId": str(ObjectId())}
        response = requests.post(f"{BASE_URL}/posts", json=data)
        self.assertEqual(response.status_code, 400)

    def test_create_post_invalid_authorId(self):
        data = {"authorId": "invalid", "content": "Some content"}
        response = requests.post(f"{BASE_URL}/posts", json=data)
        self.assertEqual(response.status_code, 400)
        res = response.json()
        self.assertEqual(res["error"], "Invalid authorId")

    def test_create_post_success(self):
        user = self.create_user("Tomas", "Jonaitis", "1970-01-01", "Bio")
        res = self.create_post(user["userId"], "Hello world!")
        self.assertEqual(res["message"], "Post created")
        self.assertIn("postId", res)

    def test_add_comment_invalid_postId(self):
        data = {"authorId": str(ObjectId()), "text": "Nice post!"}
        response = requests.post(f"{BASE_URL}/posts/invalid_id/comments", json=data)
        self.assertEqual(response.status_code, 400)
        res = response.json()
        self.assertEqual(res["error"], "Invalid postId")

    def test_add_comment_invalid_authorId(self):
        user = self.create_user("Antanas", "Petraitis", "1995-12-12", "Bio")
        post = self.create_post(user["userId"], "Post content")
        data = {"authorId": "invalid", "text": "Great!"}
        response = requests.post(f"{BASE_URL}/posts/{post['postId']}/comments", json=data)
        self.assertEqual(response.status_code, 400)
        res = response.json()
        self.assertEqual(res["error"], "Invalid authorId")

    def test_add_comment_text_too_long(self):
        user = self.create_user("Ieva", "Barauskiene", "1992-02-02", "Bio")
        post = self.create_post(user["userId"], "Content")
        long_text = "a" * 501
        data = {"authorId": user["userId"], "text": long_text}
        response = requests.post(f"{BASE_URL}/posts/{post['postId']}/comments", json=data)
        self.assertEqual(response.status_code, 400)
        res = response.json()
        self.assertEqual(res["error"], "Comment too long")

    def test_add_comment_post_not_found(self):
        data = {"authorId": str(ObjectId()), "text": "Nice!"}
        fake_post_id = str(ObjectId())
        response = requests.post(f"{BASE_URL}/posts/{fake_post_id}/comments", json=data)
        self.assertEqual(response.status_code, 404)
        res = response.json()
        self.assertEqual(res["error"], "Post not found")

    def test_add_comment_success(self):
        user = self.create_user("Mantas", "Jankauskas", "1988-08-08", "Bio")
        post = self.create_post(user["userId"], "Content")
        data = {"authorId": user["userId"], "text": "Interesting post"}
        response = requests.post(f"{BASE_URL}/posts/{post['postId']}/comments", json=data)
        self.assertEqual(response.status_code, 200)
        res = response.json()
        self.assertEqual(res["message"], "Comment added")

    def test_add_like_invalid_postId(self):
        data = {"userId": str(ObjectId())}
        response = requests.post(f"{BASE_URL}/posts/invalid_id/likes", json=data)
        self.assertEqual(response.status_code, 400)
        res = response.json()
        self.assertEqual(res["error"], "Invalid postId")

    def test_add_like_missing_userId(self):
        user = self.create_user("Giedre", "Kazlauskiene", "1906-12-09", "Bio")
        post = self.create_post(user["userId"], "Content")
        data = {}
        response = requests.post(f"{BASE_URL}/posts/{post['postId']}/likes", json=data)
        self.assertEqual(response.status_code, 400)

    def test_add_like_invalid_userId(self):
        user = self.create_user("Vytautas", "Jonaitis", "1863-07-30", "Bio")
        post = self.create_post(user["userId"], "Content")
        data = {"userId": "invalid"}
        response = requests.post(f"{BASE_URL}/posts/{post['postId']}/likes", json=data)
        self.assertEqual(response.status_code, 400)
        res = response.json()
        self.assertEqual(res["error"], "Invalid userId")

    def test_add_like_post_not_found(self):
        data = {"userId": str(ObjectId())}
        fake_post_id = str(ObjectId())
        response = requests.post(f"{BASE_URL}/posts/{fake_post_id}/likes", json=data)
        self.assertEqual(response.status_code, 404)
        res = response.json()
        self.assertEqual(res["error"], "Post not found")

    def test_add_like_duplicate(self):
        user = self.create_user("Ieva", "Martinkiene", "1999-09-09", "Bio")
        post = self.create_post(user["userId"], "Content")
        data = {"userId": user["userId"]}
        response1 = requests.post(f"{BASE_URL}/posts/{post['postId']}/likes", json=data)
        self.assertEqual(response1.status_code, 200)
        response2 = requests.post(f"{BASE_URL}/posts/{post['postId']}/likes", json=data)
        self.assertEqual(response2.status_code, 400)
        res = response2.json()
        self.assertEqual(res["error"], "User already liked this post")

    def test_follow_user_invalid_userId(self):
        data = {"followId": str(ObjectId())}
        response = requests.post(f"{BASE_URL}/users/invalid_id/follow", json=data)
        self.assertEqual(response.status_code, 400)
        res = response.json()
        self.assertEqual(res["error"], "Invalid userId")

    def test_follow_user_invalid_followId(self):
        user = self.create_user("Jokubas", "Vaitkus", "1980-01-01", "Bio")
        data = {"followId": "invalid"}
        response = requests.post(f"{BASE_URL}/users/{user['userId']}/follow", json=data)
        self.assertEqual(response.status_code, 400)
        res = response.json()
        self.assertEqual(res["error"], "Invalid followId")

    def test_follow_user_not_found(self):
        fake_user_id = str(ObjectId())
        data = {"followId": str(ObjectId())}
        response = requests.post(f"{BASE_URL}/users/{fake_user_id}/follow", json=data)
        self.assertEqual(response.status_code, 404)

    def test_follow_user_already_following(self):
        user1 = self.create_user("Karla", "Giedraitiene", "1975-10-05", "Bio")
        user2 = self.create_user("Linas", "Zabiela", "1974-11-11", "Bio")
        data = {"followId": user2["userId"]}
        resp1 = requests.post(f"{BASE_URL}/users/{user1['userId']}/follow", json=data)
        self.assertEqual(resp1.status_code, 200)
        resp2 = requests.post(f"{BASE_URL}/users/{user1['userId']}/follow", json=data)
        self.assertEqual(resp2.status_code, 400)

    def test_follow_user_success(self):
        user1 = self.create_user("Milda", "Jankauskaite", "1988-03-03", "Bio")
        user2 = self.create_user("Vincas", "Zabiela", "1985-04-04", "Bio")
        data = {"followId": user2["userId"]}
        response = requests.post(f"{BASE_URL}/users/{user1['userId']}/follow", json=data)
        self.assertEqual(response.status_code, 200)
        res = response.json()
        self.assertEqual(res["message"], "Now following the user")

    def test_unfollow_user_invalid_userId(self):
        data = {"unfollowId": str(ObjectId())}
        response = requests.post(f"{BASE_URL}/users/invalid_id/unfollow", json=data)
        self.assertEqual(response.status_code, 400)
        res = response.json()
        self.assertEqual(res["error"], "Invalid userId")

    def test_unfollow_user_invalid_unfollowId(self):
        user = self.create_user("Nora", "Petrauskiene", "1960-02-02", "Bio")
        data = {"unfollowId": "invalid"}
        response = requests.post(f"{BASE_URL}/users/{user['userId']}/unfollow", json=data)
        self.assertEqual(response.status_code, 400)
        res = response.json()
        self.assertEqual(res["error"], "Invalid unfollowId")

    def test_unfollow_user_not_following(self):
        user = self.create_user("Oskaras", "Bernotas", "1854-10-16", "Bio")
        data = {"unfollowId": str(ObjectId())}
        response = requests.post(f"{BASE_URL}/users/{user['userId']}/unfollow", json=data)
        self.assertEqual(response.status_code, 400)
        res = response.json()
        self.assertEqual(res["message"], "Not following this user")

    def test_unfollow_user_success(self):
        user1 = self.create_user("Paulius", "Grigas", "1973-09-12", "Bio")
        user2 = self.create_user("Dainius", "Zabiela", "1972-05-02", "Bio")
        follow_data = {"followId": user2["userId"]}
        unfollow_data = {"unfollowId": user2["userId"]}
        requests.post(f"{BASE_URL}/users/{user1['userId']}/follow", json=follow_data)
        response = requests.post(f"{BASE_URL}/users/{user1['userId']}/unfollow", json=unfollow_data)
        self.assertEqual(response.status_code, 200)
        res = response.json()
        self.assertEqual(res["message"], "Unfollowed the user")

    def test_get_post_likes_invalid_postId(self):
        response = requests.get(f"{BASE_URL}/posts/invalid_id/likes")
        self.assertEqual(response.status_code, 400)
        res = response.json()
        self.assertEqual(res["error"], "Invalid postId")

    def test_get_post_likes_nonexistent(self):
        fake_post_id = str(ObjectId())
        response = requests.get(f"{BASE_URL}/posts/{fake_post_id}/likes")
        self.assertEqual(response.status_code, 404)
        res = response.json()
        self.assertEqual(res["error"], "Post not found")

    def test_get_post_likes_success(self):
        user = self.create_user("Rasa", "Jankauskaite", "1969-05-05", "Bio")
        post = self.create_post(user["userId"], "Content")
        like_data = {"userId": user["userId"]}
        requests.post(f"{BASE_URL}/posts/{post['postId']}/likes", json=like_data)
        response = requests.get(f"{BASE_URL}/posts/{post['postId']}/likes")
        self.assertEqual(response.status_code, 200)
        res = response.json()
        self.assertIsInstance(res, list)
        if res:
            self.assertIn("userId", res[0])

if __name__ == '__main__':
    unittest.main()
