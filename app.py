from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re
import os
import json

app = Flask(__name__)

# Конфигурация
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-me'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///recipes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Модели
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
    ingredients = db.Column(db.Text, nullable=False)
    steps = db.Column(db.Text, nullable=False)
    cooking_time = db.Column(db.Integer)
    difficulty = db.Column(db.String(20))
    category = db.Column(db.String(50))
    image_url = db.Column(db.String(300), default='/static/img/default.jpg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def to_dict(self):
        """Преобразование рецепта в словарь для API"""
        return {
            'id': self.id,
            'title': self.title or '',
            'description': self.description or '',
            'ingredients': self.get_ingredients_list(),
            'steps': self.get_steps_list(),
            'cooking_time': self.cooking_time or 0,
            'difficulty': self.difficulty or '',
            'category': self.category or '',
            'image_url': self.image_url or '/static/img/default.jpg',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }
    
    def get_ingredients_list(self):
        """Получить ингредиенты как список"""
        if not self.ingredients:
            return []
        
        if self.ingredients.strip().startswith('['):
            try:
                ingredients_data = json.loads(self.ingredients)
                if isinstance(ingredients_data, list):
                    return ingredients_data
            except:
                pass
        
        return [line.strip() for line in self.ingredients.split('\n') if line.strip()]
    
    def get_steps_list(self):
        """Получить шаги как список"""
        if not self.steps:
            return []
        
        if self.steps.strip().startswith('['):
            try:
                steps_data = json.loads(self.steps)
                if isinstance(steps_data, list):
                    return steps_data
            except:
                pass
        
        return [line.strip() for line in self.steps.split('\n') if line.strip()]
    
    def get_ingredients_text(self):
        """Получить ингредиенты как текст для формы"""
        return self.ingredients or ''
    
    def get_steps_text(self):
        """Получить шаги как текст для формы"""
        return self.steps or ''

# Инициализация базы данных с тестовыми данными
def init_database():
    with app.app_context():
        db.create_all()
        
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', is_admin=True)
            admin.set_password('Admin123!')
            db.session.add(admin)
            db.session.commit()
            print("✅ Администратор создан: admin / Admin123!")
        
        if Recipe.query.count() == 0:
            sample_recipes = [
                {
                    'title': 'Панкейки с кленовым сиропом',
                    'description': 'Пушистые американские блинчики на завтрак',
                    'ingredients': "200г муки\n300мл молока\n2 яйца\n2 ст.л. сахара\n2 ч.л. разрыхлителя\nщепотка соли",
                    'steps': "Смешать сухие ингредиенты\nДобавить яйца и молоко, перемешать\nЖарить на сковороде по 2-3 минуты с каждой стороны\nПодавать с кленовым сиропом",
                    'cooking_time': 20,
                    'difficulty': 'Легкий',
                    'category': 'Завтрак'
                },
                {
                    'title': 'Салат Цезарь',
                    'description': 'Классический салат с курицей и сухариками',
                    'ingredients': "200г куриного филе\n100г пармезана\n1 пучок салата романо\n100г сухариков\n2 яйца\nсоус цезарь",
                    'steps': "Обжарить куриное филе\nОтварить яйца\nНарезать салат\nСмешать все ингредиенты\nЗаправить соусом",
                    'cooking_time': 25,
                    'difficulty': 'Легкий',
                    'category': 'Обед'
                }
            ]
            
            for recipe_data in sample_recipes:
                recipe = Recipe(
                    title=recipe_data['title'],
                    description=recipe_data['description'],
                    ingredients=recipe_data['ingredients'],
                    steps=recipe_data['steps'],
                    cooking_time=recipe_data['cooking_time'],
                    difficulty=recipe_data['difficulty'],
                    category=recipe_data['category'],
                    user_id=admin.id
                )
                db.session.add(recipe)
            
            db.session.commit()
            print(f"✅ Добавлено {len(sample_recipes)} тестовых рецептов")

# ========== РОУТЫ ДЛЯ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ ==========

@app.route('/')
def index():
    recipes = Recipe.query.order_by(Recipe.created_at.desc()).limit(12).all()
    return render_template('index.html', recipes=recipes)

@app.route('/search')
def search_page():
    return render_template('search.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

# ========== АДМИН-ПАНЕЛЬ ==========

@app.route('/admin')
def admin_page():
    if not session.get('is_admin'):
        flash('Требуются права администратора', 'error')
        return redirect(url_for('login_page'))
    
    recipes = Recipe.query.order_by(Recipe.created_at.desc()).all()
    users = User.query.all()
    
    return render_template('admin.html', 
                         recipes=recipes, 
                         users=users,
                         recipe_count=len(recipes),
                         user_count=len(users))

@app.route('/admin/add-recipe')
def add_recipe_page():
    if not session.get('is_admin'):
        flash('Требуются права администратора', 'error')
        return redirect(url_for('login_page'))
    return render_template('add_recipe.html')

@app.route('/admin/edit-recipe/<int:recipe_id>')
def edit_recipe_page(recipe_id):
    if not session.get('is_admin'):
        flash('Требуются права администратора', 'error')
        return redirect(url_for('login_page'))
    
    recipe = Recipe.query.get_or_404(recipe_id)
    return render_template('edit_recipe.html', 
                         recipe=recipe,
                         ingredients_text=recipe.get_ingredients_text(),
                         steps_text=recipe.get_steps_text())

# ========== API ДЛЯ УПРАВЛЕНИЯ РЕЦЕПТАМИ ==========

# Получить все рецепты
@app.route('/api/recipes')
def get_all_recipes():
    recipes = Recipe.query.order_by(Recipe.created_at.desc()).all()
    return jsonify({'recipes': [r.to_dict() for r in recipes]})

# Получить один рецепт
@app.route('/api/recipes/<int:recipe_id>')
def get_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    return jsonify({'recipe': recipe.to_dict()})

# Добавить рецепт (только админ)
@app.route('/api/recipes', methods=['POST'])
def api_add_recipe():
    if not session.get('is_admin'):
        return jsonify({'error': 'Требуются права администратора'}), 403
    
    try:
        data = request.json
        
        if not data.get('title'):
            return jsonify({'error': 'Введите название рецепта'}), 400
        
        if not data.get('ingredients'):
            return jsonify({'error': 'Добавьте хотя бы один ингредиент'}), 400
        
        if not data.get('steps'):
            return jsonify({'error': 'Добавьте шаги приготовления'}), 400
        
        cooking_time = data.get('cooking_time')
        if not cooking_time:
            return jsonify({'error': 'Введите время приготовления'}), 400
        
        try:
            cooking_time_int = int(cooking_time)
            if cooking_time_int <= 0:
                return jsonify({'error': 'Введите корректное время приготовления (больше 0)'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Время приготовления должно быть числом'}), 400
        
        # Обработка ингредиентов - преобразуем список в текст
        ingredients_data = data['ingredients']
        if isinstance(ingredients_data, list):
            ingredients_text = '\n'.join([str(item).strip() for item in ingredients_data if str(item).strip()])
        else:
            ingredients_text = str(ingredients_data).strip()
        
        # Обработка шагов - преобразуем список в текст
        steps_data = data['steps']
        if isinstance(steps_data, list):
            steps_text = '\n'.join([str(item).strip() for item in steps_data if str(item).strip()])
        else:
            steps_text = str(steps_data).strip()
        
        # Создание рецепта
        recipe = Recipe(
            title=str(data['title']).strip(),
            description=str(data.get('description', '')).strip(),
            ingredients=ingredients_text,
            steps=steps_text,
            cooking_time=cooking_time_int,
            difficulty=data.get('difficulty', 'Средний'),
            category=data.get('category', 'Основное'),
            image_url=data.get('image_url', '/static/img/default.jpg'),
            user_id=session['user_id']
        )
        
        db.session.add(recipe)
        db.session.commit()
        
        return jsonify({
            'message': 'Рецепт успешно добавлен!',
            'recipe': recipe.to_dict()
        }), 201
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

# Обновить рецепт (только админ)
@app.route('/api/recipes/update/<int:recipe_id>', methods=['PUT'])
def api_update_recipe(recipe_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Требуются права администратора'}), 403
    
    recipe = Recipe.query.get_or_404(recipe_id)
    
    try:
        data = request.json
        
        if 'title' in data:
            recipe.title = str(data['title']).strip()
        
        if 'description' in data:
            recipe.description = str(data['description']).strip()
        
        if 'ingredients' in data:
            ingredients_data = data['ingredients']
            if isinstance(ingredients_data, list):
                recipe.ingredients = '\n'.join([str(item).strip() for item in ingredients_data if str(item).strip()])
            else:
                recipe.ingredients = str(ingredients_data).strip()
        
        if 'steps' in data:
            steps_data = data['steps']
            if isinstance(steps_data, list):
                recipe.steps = '\n'.join([str(item).strip() for item in steps_data if str(item).strip()])
            else:
                recipe.steps = str(steps_data).strip()
        
        if 'cooking_time' in data:
            try:
                recipe.cooking_time = int(data['cooking_time'])
            except (ValueError, TypeError):
                return jsonify({'error': 'Время приготовления должно быть числом'}), 400
        
        if 'difficulty' in data:
            recipe.difficulty = data['difficulty']
        
        if 'category' in data:
            recipe.category = data['category']
        
        if 'image_url' in data:
            recipe.image_url = data['image_url']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Рецепт успешно обновлен!',
            'recipe': recipe.to_dict()
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

# Удалить рецепт (только админ)
@app.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
def api_delete_recipe(recipe_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Требуются права администратора'}), 403
    
    recipe = Recipe.query.get_or_404(recipe_id)
    title = recipe.title
    
    db.session.delete(recipe)
    db.session.commit()
    
    return jsonify({
        'message': f'Рецепт "{title}" успешно удален!'
    })

# ========== ПОИСК РЕЦЕПТОВ ==========

@app.route('/api/recipes/search')
def search_recipes():
    """Поиск рецептов (совметимость с main.js)"""
    return perform_search()

@app.route('/api/search')
def perform_search():
    from sqlalchemy import or_
    
    query = request.args.get('q', '').strip()
    ingredients = request.args.get('ingredients', '').strip()
    mode = request.args.get('mode', 'any')
    category = request.args.get('category', '').strip()
    difficulty = request.args.get('difficulty', '').strip()
    time = request.args.get('time', '').strip()
    
    recipes_query = Recipe.query
    
    # Поиск по названию и описанию
    if query:
        recipes_query = recipes_query.filter(
            or_(
                Recipe.title.ilike(f'%{query}%'),
                Recipe.description.ilike(f'%{query}%')
            )
        )
    
    # Поиск по ингредиентам
    if ingredients:
        ingredients_list = [ing.strip().lower() for ing in ingredients.split(',') if ing.strip()]
        
        if ingredients_list:
            if mode == 'all':
                for ing in ingredients_list:
                    recipes_query = recipes_query.filter(
                        Recipe.ingredients.ilike(f'%{ing}%')
                    )
            else:
                conditions = []
                for ing in ingredients_list:
                    conditions.append(Recipe.ingredients.ilike(f'%{ing}%'))
                if conditions:
                    recipes_query = recipes_query.filter(or_(*conditions))
    
    # Фильтр по категории
    if category:
        recipes_query = recipes_query.filter(Recipe.category == category)
    
    # Фильтр по сложности
    if difficulty:
        recipes_query = recipes_query.filter(Recipe.difficulty == difficulty)
    
    # Фильтр по времени
    if time:
        try:
            max_time = int(time)
            recipes_query = recipes_query.filter(Recipe.cooking_time <= max_time)
        except ValueError:
            pass
    
    recipes = recipes_query.order_by(Recipe.created_at.desc()).all()
    
    return jsonify({
        'recipes': [r.to_dict() for r in recipes],
        'count': len(recipes)
    })

# ========== API ДЛЯ АУТЕНТИФИКАЦИИ ==========

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Заполните все поля'}), 400
    
    if re.search('[а-яА-Я]', data['username']):
        return jsonify({'error': 'Логин должен содержать только латинские буквы'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Пользователь уже существует'}), 400
    
    user = User(
        username=data['username'],
        email=data.get('email', f"{data['username']}@example.com")
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'Регистрация успешна!'}), 201

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    
    user = User.query.filter_by(username=data.get('username')).first()
    
    if user and user.check_password(data.get('password', '')):
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        
        return jsonify({
            'message': 'Вход выполнен!',
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
    return jsonify({'message': 'Выход выполнен!'})

@app.route('/api/user/delete', methods=['POST'])
def api_delete_account():
    if not session.get('user_id'):
        return jsonify({'error': 'Не авторизован'}), 401
    
    user = User.query.get(session['user_id'])
    
    if user.is_admin:
        return jsonify({'error': 'Нельзя удалить администратора'}), 403
    
    Recipe.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    
    session.clear()
    return jsonify({'message': 'Аккаунт удален!'})

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

@app.context_processor
def inject_user():
    user_info = {
        'is_authenticated': 'user_id' in session,
        'username': session.get('username'),
        'is_admin': session.get('is_admin', False)
    }
    return dict(user=user_info)

@app.before_request
def before_request():
    if not hasattr(app, 'db_initialized'):
        init_database()
        app.db_initialized = True

# ========== ДЕБАГ РЕЦЕПТОВ ==========

@app.route('/debug/recipes')
def debug_recipes():
    """Страница для отладки - показывает все рецепты в базе"""
    recipes = Recipe.query.all()
    result = []
    for recipe in recipes:
        result.append({
            'id': recipe.id,
            'title': recipe.title,
            'ingredients_raw': recipe.ingredients[:100] + '...' if recipe.ingredients and len(recipe.ingredients) > 100 else recipe.ingredients,
            'steps_raw': recipe.steps[:100] + '...' if recipe.steps and len(recipe.steps) > 100 else recipe.steps,
            'category': recipe.category,
            'cooking_time': recipe.cooking_time,
            'difficulty': recipe.difficulty
        })
    return jsonify({'recipes': result, 'count': len(result)})

# ========== ЗАПУСК ==========

if __name__ == '__main__':
    print("=" * 50)
    print("🍽️  Сайт рецептов Полины")
    print("=" * 50)
    print("Данные для входа:")
    print("👑 Администратор: admin / Admin123!")
    print("\nСсылки:")
    print("🌐 Главная страница: http://localhost:5001")
    print("👑 Админ-панель: http://localhost:5001/admin")
    print("🔍 Поиск рецептов: http://localhost:5001/search")
    print("🐛 Отладка рецептов: http://localhost:5001/debug/recipes")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5001)
    