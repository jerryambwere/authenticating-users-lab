#!/usr/bin/env python3

from flask import Flask, make_response, jsonify, request, session
from flask_migrate import Migrate
from flask_restful import Api, Resource

from models import db, Article, User

app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

class ClearSession(Resource):
    def delete(self):
        session['page_views'] = None
        session['user_id'] = None
        return {}, 204

class IndexArticle(Resource):
    def get(self):
        articles = [article.to_dict() for article in Article.query.all()]
        return articles, 200

class ShowArticle(Resource):
    def get(self, id):
        session['page_views'] = 0 if not session.get('page_views') else session.get('page_views')
        session['page_views'] += 1

        if session['page_views'] <= 3:
            article = Article.query.filter(Article.id == id).first()
            if article:
                return article.to_dict(), 200  # Return the dictionary directly, Flask will serialize to JSON
            else:
                return {'message': 'Article not found'}, 404

        return {'message': 'Maximum pageview limit reached'}, 401

class Login(Resource):
    def post(self):
        '''Logs the user in by username and adds user_id to session at /login.'''
        data = request.get_json()
        username = data.get('username')

        if not username:
            return {'message': 'Username is required'}, 400
        
        # Retrieve user by username
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return {'message': 'User not found'}, 404
        
        # Set the user_id in the session
        session['user_id'] = user.id
        
        # Return user data as dictionary (Flask will serialize to JSON)
        return {'id': user.id, 'username': user.username}, 200

class Logout(Resource):
    def delete(self):
        '''Logs the user out by clearing the session.'''
        session.pop('user_id', None)  # Remove user_id from session
        return '', 204

class CheckSession(Resource):
    def get(self):
        '''Checks if a user is logged in by checking the session.'''
        user_id = session.get('user_id')

        if user_id:
            # Retrieve the user from the database
            user = User.query.get(user_id)
            
            if user:
                # Return user data as dictionary (Flask will serialize to JSON)
                return {'id': user.id, 'username': user.username}, 200
        # If user_id is not in session, return Unauthorized
        return {'message': 'Unauthorized'}, 401

api.add_resource(CheckSession, '/check_session')
api.add_resource(Logout, '/logout')
api.add_resource(Login,'/login')
api.add_resource(ClearSession, '/clear')
api.add_resource(IndexArticle, '/articles')
api.add_resource(ShowArticle, '/articles/<int:id>')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
