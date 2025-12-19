from models import db, User, Recipe
import json

def init_db(app):
    """Инициализация базы данных"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        # Создаем администратора, если его нет
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('Admin123!')
            db.session.add(admin)
            db.session.commit()
        
        # Добавляем начальные рецепты (минимум 100)
        if Recipe.query.count() < 100:
            add_sample_recipes()

def add_sample_recipes():
    """Добавление примерных рецептов"""
    sample_recipes = [
        {
            'title': 'Панкейки с кленовым сиропом',
            'description': 'Пушистые американские блинчики',
            'ingredients': ['мука 200г', 'молоко 300мл', 'яйца 2шт', 'сахар 2ст.л.', 'разрыхлитель 2ч.л.'],
            'steps': ['Смешать сухие ингредиенты', 'Добавить яйца и молоко', 'Жарить на сковороде'],
            'cooking_time': 20,
            'difficulty': 'Легкий',
            'category': 'Завтрак',
            'image_url': '/static/img/pancakes.jpg'
        },
        # ... добавь еще 99+ рецептов разных категорий
    ]
    
    admin = User.query.filter_by(username='admin').first()
    for recipe_data in sample_recipes:
        recipe = Recipe(
            title=recipe_data['title'],
            description=recipe_data['description'],
            ingredients=str(recipe_data['ingredients']),
            steps=str(recipe_data['steps']),
            cooking_time=recipe_data['cooking_time'],
            difficulty=recipe_data['difficulty'],
            category=recipe_data['category'],
            image_url=recipe_data['image_url'],
            user_id=admin.id
        )
        db.session.add(recipe)
    
    db.session.commit()
    