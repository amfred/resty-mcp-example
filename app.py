from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "resty.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(100))
    age = db.Column(db.Integer)
    description = db.Column(db.Text)
    is_adopted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'species': self.species,
            'breed': self.breed,
            'age': self.age,
            'description': self.description,
            'is_adopted': self.is_adopted,
            'created_at': self.created_at.isoformat()
        }

# Routes
@app.route('/')
def home():
    return jsonify({
        'message': 'Welcome to Resty MCP Example - Pet Adoption API!',
        'endpoints': {
            'GET /pets': 'Get all pets',
            'POST /pets': 'Add a new pet',
            'GET /pets/<id>': 'Get a specific pet',
            'PUT /pets/<id>/adopt': 'Adopt a pet by ID',
            'PUT /pets/adopt?name=<name>': 'Adopt a pet by name',
            'DELETE /pets/<id>': 'Delete a pet',
            'GET /pets/search': 'Search pets with filters'
        }
    })

@app.route('/pets', methods=['GET'])
def get_pets():
    pets = Pet.query.all()
    return jsonify([pet.to_dict() for pet in pets])

@app.route('/pets', methods=['POST'])
def create_pet():
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('species'):
        return jsonify({'error': 'Name and species are required'}), 400
    
    pet = Pet(
        name=data['name'],
        species=data['species'],
        breed=data.get('breed'),
        age=data.get('age'),
        description=data.get('description')
    )
    
    db.session.add(pet)
    db.session.commit()
    
    return jsonify(pet.to_dict()), 201

@app.route('/pets/<int:pet_id>', methods=['GET'])
def get_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    return jsonify(pet.to_dict())

@app.route('/pets/<int:pet_id>/adopt', methods=['PUT'])
def adopt_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    
    if pet.is_adopted:
        return jsonify({'error': 'Pet is already adopted'}), 400
    
    pet.is_adopted = True
    db.session.commit()
    
    return jsonify(pet.to_dict())

@app.route('/pets/<int:pet_id>', methods=['DELETE'])
def delete_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    db.session.delete(pet)
    db.session.commit()
    
    return jsonify({'message': 'Pet deleted successfully'})

@app.route('/pets/adopt', methods=['PUT'])
def adopt_pet_by_name():
    name = request.args.get('name')
    
    if not name:
        return jsonify({'error': 'Name parameter is required'}), 400
    
    # Find pet by name (case-insensitive)
    pet = Pet.query.filter(Pet.name.ilike(f'%{name}%')).first()
    
    if not pet:
        return jsonify({'error': f'No pet found with name containing "{name}"'}), 404
    
    if pet.is_adopted:
        return jsonify({'error': f'{pet.name} is already adopted'}), 400
    
    pet.is_adopted = True
    db.session.commit()
    
    return jsonify({
        'message': f'{pet.name} has been successfully adopted!',
        'pet': pet.to_dict()
    })

@app.route('/pets/search', methods=['GET'])
def search_pets():
    species = request.args.get('species')
    breed = request.args.get('breed')
    available_only = request.args.get('available_only', 'false').lower() == 'true'
    
    query = Pet.query
    
    if species:
        query = query.filter(Pet.species.ilike(f'%{species}%'))
    if breed:
        query = query.filter(Pet.breed.ilike(f'%{breed}%'))
    if available_only:
        query = query.filter(Pet.is_adopted == False)
    
    pets = query.all()
    return jsonify([pet.to_dict() for pet in pets])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Add some sample data if the database is empty
        if Pet.query.count() == 0:
            sample_pets = [
                Pet(name='Buddy', species='Dog', breed='Golden Retriever', age=3, description='Friendly and energetic'),
                Pet(name='Whiskers', species='Cat', breed='Persian', age=2, description='Calm and cuddly'),
                Pet(name='Tweety', species='Bird', breed='Canary', age=1, description='Sings beautifully'),
                Pet(name='Max', species='Dog', breed='Labrador', age=5, description='Great with kids'),
                Pet(name='Luna', species='Cat', breed='Siamese', age=1, description='Playful and curious')
            ]
            
            for pet in sample_pets:
                db.session.add(pet)
            db.session.commit()
            print("Sample pets added to database!")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
