from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    ingredients = db.Column(db.Text, nullable=False)  # JSON строка
    steps = db.Column(db.Text, nullable=False)        # JSON строка
    cooking_time = db.Column(db.Integer)              # в минутах
    difficulty = db.Column(db.String(20))             # Легкий/Средний/Сложный
    category = db.Column(db.String(50))              # Завтрак, Обед, Ужин, Десерт
    image_url = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Связь с пользователем
    user = db.relationship('User', backref=db.backref('recipes', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'ingredients': eval(self.ingredients) if self.ingredients else [],
            'steps': eval(self.steps) if self.steps else [],
            'cooking_time': self.cooking_time,
            'difficulty': self.difficulty,
            'category': self.category,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat()
        }
    