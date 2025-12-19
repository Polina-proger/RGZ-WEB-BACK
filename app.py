from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from config import Config
from database import init_db, db
from models import User, Recipe
import re
import json

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Инициализация БД
init_db(app)

# ========== Валидация ==========
def validate_username(username):
    """Проверка логина: только латинские буквы, цифры и _-."""
    pattern = r'^[a-zA-Z0-9_-]{3,50}$'
    return bool(re.match(pattern, username))

def validate_password(password):
    """Проверка пароля: минимум 8 символов, буквы, цифры и знаки препинания."""
    if len(password) < 8:
        return False
    # Проверка на русские буквы
    if re.search('[а-яА-Я]', password):
        return False
    # Должны быть буквы и цифры
    if not re.search('[a-zA-Z]', password) or not re.search('[0-9]', password):
        return False
    return True

def validate_email(email):
    """Простая валидация email."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

# ========== API Роуты ==========
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    
    # Валидация
    if not all(k in data for k in ['username', 'email', 'password']):
        return jsonify({'error': 'Не все поля заполнены'}), 400
    
    if not validate_username(data['username']):
        return jsonify({'error': 'Логин должен содержать только латинские буквы, цифры, _ или -'}), 400
    
    if not validate_email(data['email']):
        return jsonify({'error': 'Некорректный email'}), 400
    
    if not validate_password(data['password']):
        return jsonify({'error': 'Пароль должен быть минимум 8 символов, содержать буквы и цифры (без русских букв)'}), 400
    
    # Проверка существования пользователя
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Пользователь уже существует'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email уже используется'}), 400
    
    # Создание пользователя
    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'Регистрация успешна'}), 201

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    
    user = User.query.filter_by(username=data.get('username')).first()
    
    if user and user.check_password(data.get('password', '')):
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        session.permanent = True
        
        return jsonify({
            'message': 'Вход выполнен',
            'user': {
                'id': user.id,
                'username': user.username,
                'is_admin': user.is_admin
            }
        })
    
    return jsonify({'error': 'Неверный логин или пароль'}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'message': 'Выход выполнен'})

@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    """Получение рецептов с пагинацией и фильтрацией"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    category = request.args.get('category')
    
    query = Recipe.query
    
    if category:
        query = query.filter_by(category=category)
    
    recipes = query.order_by(Recipe.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'recipes': [r.to_dict() for r in recipes.items],
        'total': recipes.total,
        'pages': recipes.pages,
        'current_page': page
    })

@app.route('/api/recipes/search', methods=['GET'])
def search_recipes():
    """Поиск рецептов по названию и ингредиентам"""
    query = request.args.get('q', '')
    ingredients = request.args.get('ingredients', '')
    search_mode = request.args.get('mode', 'any')  # 'any' или 'all'
    
    recipes_query = Recipe.query
    
    # Поиск по названию
    if query:
        recipes_query = recipes_query.filter(
            Recipe.title.ilike(f'%{query}%')
        )
    
    # Поиск по ингредиентам
    if ingredients:
        ingredients_list = [i.strip().lower() for i in ingredients.split(',')]
        
        if search_mode == 'all':
            # Все ингредиенты должны быть в рецепте
            for ing in ingredients_list:
                recipes_query = recipes_query.filter(
                    Recipe.ingredients.ilike(f'%{ing}%')
                )
        else:
            # Хотя бы один ингредиент
            from sqlalchemy import or_
            conditions = []
            for ing in ingredients_list:
                conditions.append(Recipe.ingredients.ilike(f'%{ing}%'))
            recipes_query = recipes_query.filter(or_(*conditions))
    
    recipes = recipes_query.limit(50).all()
    return jsonify({'recipes': [r.to_dict() for r in recipes]})

@app.route('/api/recipes', methods=['POST'])
def add_recipe():
    """Добавление нового рецепта (только для админа)"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Требуются права администратора'}), 403
    
    data = request.get_json()
    
    # Валидация
    if not data.get('title') or not data.get('ingredients') or not data.get('steps'):
        return jsonify({'error': 'Заполните обязательные поля'}), 400
    
    if data.get('cooking_time', 0) <= 0:
        return jsonify({'error': 'Время приготовления должно быть положительным'}), 400
    
    recipe = Recipe(
        title=data['title'],
        description=data.get('description', ''),
        ingredients=str(data['ingredients']),
        steps=str(data['steps']),
        cooking_time=data['cooking_time'],
        difficulty=data.get('difficulty', 'Средний'),
        category=data.get('category', 'Основное'),
        image_url=data.get('image_url', '/static/img/default.jpg'),
        user_id=session['user_id']
    )
    
    db.session.add(recipe)
    db.session.commit()
    
    return jsonify({'message': 'Рецепт добавлен', 'id': recipe.id}), 201

@app.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    """Обновление рецепта (только для админа)"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Требуются права администратора'}), 403
    
    recipe = Recipe.query.get_or_404(recipe_id)
    data = request.get_json()
    
    # Обновление полей
    if 'title' in data:
        recipe.title = data['title']
    if 'ingredients' in data:
        recipe.ingredients = str(data['ingredients'])
    if 'steps' in data:
        recipe.steps = str(data['steps'])
    if 'cooking_time' in data and data['cooking_time'] > 0:
        recipe.cooking_time = data['cooking_time']
    
    db.session.commit()
    return jsonify({'message': 'Рецепт обновлен'})

@app.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    """Удаление рецепта (только для админа)"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Требуются права администратора'}), 403
    
    recipe = Recipe.query.get_or_404(recipe_id)
    db.session.delete(recipe)
    db.session.commit()
    
    return jsonify({'message': 'Рецепт удален'})

@app.route('/api/user/delete', methods=['POST'])
def delete_account():
    """Удаление аккаунта пользователя"""
    if not session.get('user_id'):
        return jsonify({'error': 'Не авторизован'}), 401
    
    user = User.query.get(session['user_id'])
    
    # Админа нельзя удалить через этот метод
    if user.is_admin:
        return jsonify({'error': 'Нельзя удалить администратора'}), 403
    
    # Удаляем рецепты пользователя
    Recipe.query.filter_by(user_id=user.id).delete()
    
    # Удаляем пользователя
    db.session.delete(user)
    db.session.commit()
    
    session.clear()
    return jsonify({'message': 'Аккаунт удален'})

# ========== HTML Роуты ==========
@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/search')
def search_page():
    return render_template('search.html')

@app.route('/admin')
def admin_page():
    if not session.get('is_admin'):
        return redirect(url_for('login_page'))
    return render_template('admin.html')

@app.route('/add-recipe')
def add_recipe_page():
    if not session.get('is_admin'):
        return redirect(url_for('login_page'))
    return render_template('add_recipe.html')

# ========== Контекст ==========
@app.context_processor
def inject_user():
    """Добавляет пользователя во все шаблоны"""
    user_info = {
        'is_authenticated': 'user_id' in session,
        'username': session.get('username'),
        'is_admin': session.get('is_admin', False)
    }
    return dict(user=user_info)

if __name__ == '__main__':
    app.run(debug=True)
    