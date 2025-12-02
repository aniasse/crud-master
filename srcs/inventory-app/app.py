import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc

# Initialize Flask app
app = Flask(__name__)

# --- Database Configuration ---
db_user = os.environ.get('INVENTORY_DB_USER', 'inventory_user')
db_password = os.environ.get('INVENTORY_DB_PASSWORD', 'inventory_password')
db_name = os.environ.get('INVENTORY_DB_NAME', 'movies_db')
db_host = 'localhost'

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Movie Model ---
class Movie(db.Model):
    __tablename__ = 'movies'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description
        }

# --- Utility to create tables ---
def create_tables():
    with app.app_context():
        print("Creating database tables...")
        try:
            db.create_all()
            print("Tables created successfully.")
        except Exception as e:
            print(f"Error creating tables: {e}")

# --- API Endpoints ---

@app.route('/api/movies', methods=['POST'])
def create_movie():
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400
    
    new_movie = Movie(title=data['title'], description=data.get('description'))
    
    try:
        db.session.add(new_movie)
        db.session.commit()
        return jsonify(new_movie.to_dict()), 201
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/movies', methods=['GET'])
def get_movies():
    title_query = request.args.get('title')
    if title_query:
        movies = Movie.query.filter(Movie.title.ilike(f'%{title_query}%')).all()
    else:
        movies = Movie.query.all()
    
    return jsonify([movie.to_dict() for movie in movies]), 200

@app.route('/api/movies/<int:id>', methods=['GET'])
def get_movie_by_id(id):
    movie = db.session.get(Movie, id)
    if movie is None:
        return jsonify({'error': 'Movie not found'}), 404
    return jsonify(movie.to_dict()), 200

@app.route('/api/movies/<int:id>', methods=['PUT'])
def update_movie(id):
    movie = db.session.get(Movie, id)
    if movie is None:
        return jsonify({'error': 'Movie not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400

    movie.title = data.get('title', movie.title)
    movie.description = data.get('description', movie.description)
    
    try:
        db.session.commit()
        return jsonify(movie.to_dict()), 200
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/movies/<int:id>', methods=['DELETE'])
def delete_movie(id):
    movie = db.session.get(Movie, id)
    if movie is None:
        return jsonify({'error': 'Movie not found'}), 404
    
    try:
        db.session.delete(movie)
        db.session.commit()
        return '', 204
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/movies', methods=['DELETE'])
def delete_all_movies():
    try:
        num_deleted = db.session.query(Movie).delete()
        db.session.commit()
        return jsonify({'message': f'{num_deleted} movies deleted.'}), 200
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# --- Health Check Endpoint ---
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    # Create tables before running the app
    create_tables()
    # Run Flask app
    app.run(host='0.0.0.0', port=os.environ.get('INVENTORY_API_PORT', 8080))
