# Bloom Server

Проект, сгенерированный с помощью Cursor для проверки гипотезы о защите API с использованием Bloom фильтров.

## Описание

Этот проект демонстрирует нестандартный подход к защите API от прямых запросов. Вместо традиционных методов аутентификации, используется Bloom фильтр для отслеживания посещенных URL в рамках сессии пользователя.

### Основные особенности

- Использование Bloom фильтров для хранения информации о посещенных URL
- Защита API от прямых запросов без посещения веб-интерфейса
- Отслеживание сессий пользователей
- Автоматическое создание и управление сессиями
- Поддержка множества параллельных сессий

### Технические детали

- FastAPI для бэкенда
- Bloom фильтры для хранения URL в памяти
- Сессии на основе cookie
- E2E тесты для проверки функциональности

## Установка и запуск

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Запустите сервер:
```bash
uvicorn main:app --reload
```

3. Запустите тесты:
```bash
pytest test_e2e.py -v
```

## Как это работает

1. При первом запросе пользователю выдается cookie с уникальным session_id
2. Каждый посещенный URL добавляется в Bloom фильтр сессии
3. API эндпоинты проверяют наличие посещения главной страницы в фильтре
4. Если главная страница не была посещена, API возвращает ошибку 400

## Тестирование

Проект включает набор E2E тестов, проверяющих:
- Защиту API от прямых запросов
- Сохранение сессий между запросами
- Работу с множеством параллельных сессий
- Корректность работы Bloom фильтров

## Гипотеза

Этот проект проверяет гипотезу о том, что можно защитить API от прямых запросов, не используя традиционные методы аутентификации, а вместо этого отслеживая поведение пользователя через Bloom фильтры. Это может быть полезно в случаях, когда:

- Нужна простая защита от прямых запросов
- Важно сохранить анонимность пользователей
- Требуется минимальная настройка
- Нужна защита от простых ботов

## API Documentation

After starting the server, the API documentation is available at the following addresses:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc