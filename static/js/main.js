// Основные функции сайта

// Проверка авторизации
function checkAuth() {
    return fetch('/api/check-auth')
        .then(res => res.json())
        .catch(() => ({ is_authenticated: false }));
}

// Вход
async function login(username, password) {
    const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    
    if (response.ok) {
        showNotification('Вход выполнен успешно!', 'success');
        setTimeout(() => window.location.href = '/', 1500);
    } else {
        showNotification(data.error || 'Ошибка входа', 'error');
    }
    
    return data;
}

// Выход
async function logout() {
    const response = await fetch('/api/logout', {
        method: 'POST'
    });
    
    const data = await response.json();
    showNotification(data.message, 'success');
    setTimeout(() => window.location.href = '/', 1000);
}

// Удаление аккаунта
async function deleteAccount() {
    if (!confirm('Вы уверены? Это действие нельзя отменить.')) return;
    
    const response = await fetch('/api/user/delete', {
        method: 'POST'
    });
    
    const data = await response.json();
    
    if (response.ok) {
        showNotification(data.message, 'success');
        setTimeout(() => window.location.href = '/', 1500);
    } else {
        showNotification(data.error, 'error');
    }
}

// Поиск рецептов
async function searchRecipes(query, ingredients, mode = 'any') {
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (ingredients) params.append('ingredients', ingredients);
    params.append('mode', mode);
    
    const response = await fetch(`/api/recipes/search?${params}`);
    return await response.json();
}

// Добавление рецепта (для админа)
async function addRecipe(recipeData) {
    const response = await fetch('/api/recipes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(recipeData)
    });
    
    const data = await response.json();
    
    if (response.ok) {
        showNotification('Рецепт добавлен!', 'success');
        return data;
    } else {
        showNotification(data.error, 'error');
        throw new Error(data.error);
    }
}

// Уведомления
function showNotification(message, type = 'info') {
    // Создаем элемент уведомления
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>
    `;
    
    // Стили для уведомления
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#a3d9b1' : '#ff6b6b'};
        color: white;
        border-radius: 10px;
        display: flex;
        align-items: center;
        gap: 10px;
        z-index: 9999;
        animation: slideIn 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    `;
    
    document.body.appendChild(notification);
    
    // Автоматическое удаление через 5 секунд
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// Анимации для уведомлений
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Загрузка рецептов на главной
async function loadRecipes(page = 1) {
    const response = await fetch(`/api/recipes?page=${page}&per_page=12`);
    const data = await response.json();
    
    if (data.recipes && data.recipes.length > 0) {
        renderRecipes(data.recipes);
        renderPagination(data);
    } else {
        document.getElementById('recipes-container').innerHTML = `
            <div class="no-recipes">
                <i class="fas fa-utensils" style="font-size: 4rem; color: var(--primary);"></i>
                <h3>Рецепты не найдены</h3>
                <p>Будьте первым, кто добавит рецепт!</p>
            </div>
        `;
    }
}

// Рендер рецептов
function renderRecipes(recipes) {
    const container = document.getElementById('recipes-container');
    if (!container) return;
    
    container.innerHTML = recipes.map(recipe => `
        <div class="recipe-card">
            ${recipe.image_url ? `
                <img src="${recipe.image_url}" alt="${recipe.title}" class="recipe-image" 
                     onerror="this.src='/static/img/default.jpg'">
            ` : ''}
            
            <div class="recipe-content">
                <h3 class="recipe-title">${recipe.title}</h3>
                
                <div class="recipe-meta">
                    <span><i class="fas fa-clock"></i> ${recipe.cooking_time} мин</span>
                    <span><i class="fas fa-fire"></i> ${recipe.difficulty}</span>
                    <span><i class="fas fa-tag"></i> ${recipe.category}</span>
                </div>
                
                <div class="recipe-ingredients">
                    ${recipe.ingredients.slice(0, 3).map(ing => `
                        <span class="ingredient-tag">${ing}</span>
                    `).join('')}
                    ${recipe.ingredients.length > 3 ? 
                        `<span class="ingredient-tag">+${recipe.ingredients.length - 3} еще</span>` : ''}
                </div>
                
                <div class="recipe-steps">
                    <h4><i class="fas fa-list-ol"></i> Шаги:</h4>
                    ${recipe.steps.slice(0, 2).map((step, i) => `
                        <div class="step-item">${i + 1}. ${step}</div>
                    `).join('')}
                    ${recipe.steps.length > 2 ? 
                        '<div class="step-item">...</div>' : ''}
                </div>
                
                <button class="btn-view" onclick="viewRecipe(${recipe.id})">
                    <i class="fas fa-eye"></i> Подробнее
                </button>
            </div>
        </div>
    `).join('');
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем, на главной ли мы странице
    if (document.getElementById('recipes-container')) {
        loadRecipes();
    }
    
    // Обработка форм
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const username = this.querySelector('[name="username"]').value;
            const password = this.querySelector('[name="password"]').value;
            login(username, password);
        });
    }
    
    // Обработка поиска
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const query = this.querySelector('[name="query"]').value;
            const ingredients = this.querySelector('[name="ingredients"]').value;
            const mode = document.querySelector('.mode-btn.active')?.dataset.mode || 'any';
            
            const result = await searchRecipes(query, ingredients, mode);
            if (result.recipes) {
                renderRecipes(result.recipes);
            }
        });
    }
});
