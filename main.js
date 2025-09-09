// Функция для обновления даты и дня недели
function updateDate() {
    const now = new Date();
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    const dateString = now.toLocaleDateString('ru-RU', options);
    const dayString = now.toLocaleDateString('ru-RU', { weekday: 'long' });
    
    document.querySelector('.date').textContent = dateString;
    document.querySelector('.day').textContent = dayString.charAt(0).toUpperCase() + dayString.slice(1);
}

// Добавляем интерактивность для уроков
function setupLessonInteractions() {
    document.querySelectorAll('.lesson').forEach(lesson => {
        lesson.addEventListener('click', () => {
            // Снимаем выделение со всех уроков
            document.querySelectorAll('.lesson').forEach(l => {
                l.classList.remove('active');
            });
            // Выделяем текущий урок
            lesson.classList.add('active');
            
            // Сохраняем в localStorage выбранный урок
            localStorage.setItem('selectedLesson', lesson.querySelector('.subject').textContent);
        });
    });
}

// Функция переключения темы
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    // Устанавливаем новую тему
    document.documentElement.setAttribute('data-theme', newTheme);
    
    // Сохраняем выбор темы
    localStorage.setItem('theme', newTheme);
    
    // Обновляем текст кнопки
    updateThemeButtonText();
}

// Обновляем текст кнопки в зависимости от темы
function updateThemeButtonText() {
    const themeToggle = document.querySelector('.theme-toggle');
    const currentTheme = document.documentElement.getAttribute('data-theme');
    
    if (currentTheme === 'dark') {
        themeToggle.textContent = ' Светлая тема';
    } else {
        themeToggle.textContent = ' Тёмная тема';
    }
}

// Создаем кнопку переключения темы
function createThemeToggle() {
    const themeToggle = document.createElement('button');
    themeToggle.className = 'theme-toggle';
    themeToggle.textContent = ' Тёмная тема';
    
    themeToggle.addEventListener('click', toggleTheme);
    
    document.body.appendChild(themeToggle);
}

// Восстанавливаем настройки из localStorage
function restoreSettings() {
    // Восстанавливаем тему
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    } else {
        // Проверяем системные настройки
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (prefersDark) {
            document.documentElement.setAttribute('data-theme', 'dark');
        }
    }
    
    // Обновляем текст кнопки
    updateThemeButtonText();
    
    // Восстанавливаем выбранный урок (если есть)
    const selectedLesson = localStorage.getItem('selectedLesson');
    if (selectedLesson) {
        document.querySelectorAll('.lesson').forEach(lesson => {
            if (lesson.querySelector('.subject').textContent === selectedLesson) {
                lesson.classList.add('active');
            }
        });
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    updateDate();
    setupLessonInteractions();
    createThemeToggle();
    restoreSettings();
    
    // Обновляем дату каждую минуту (на случай, если страница открыта долго)
    setInterval(updateDate, 60000);
    
    // Слушаем изменения системной темы
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            const newTheme = e.matches ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            updateThemeButtonText();
        }
    });
});