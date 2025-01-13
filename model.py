from flask_pymongo import PyMongo

# Initialize PyMongo here (or you can do it in your main app file)
mongo = PyMongo()

class Users:
    @staticmethod
    def find_one(query):
        return mongo.db.users.find_one(query)

    @staticmethod
    def save_user(user_data):
        mongo.db.users.insert_one(user_data)

    # You can add other methods for interacting with the database as needed
