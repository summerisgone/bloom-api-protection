from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
import os
from typing import List, Dict, Callable
import re
import uuid
from datetime import datetime, timedelta
from functools import wraps
from bloom_filter import session_filters

app = FastAPI(
    title="Bloom Server",
    description="FastAPI server for Bloom application",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Middleware для установки cookie сессии
@app.middleware("http")
async def session_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # Проверяем наличие cookie сессии
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        # Создаем новую сессию
        session_id = str(uuid.uuid4())
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            samesite="lax",
            path="/"
        )
    
    # Добавляем URL в фильтр сессии
    session_filters.add_url(session_id, request.url.path)
    
    return response

class SearchQuery(BaseModel):
    query: str

class SearchResult(BaseModel):
    filename: str
    matches: List[Dict[str, str]]

class SuggestionResult(BaseModel):
    text: str
    filename: str

def search_in_file(filepath: str, query: str, context_lines: int = 2) -> List[Dict[str, str]]:
    matches = []
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                if query.lower() in line.lower():
                    # Получаем контекст
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    context = ''.join(lines[start:end])
                    
                    # Подсвечиваем найденный текст
                    highlighted_line = re.sub(
                        f'({query})',
                        r'<mark>\1</mark>',
                        line,
                        flags=re.IGNORECASE
                    )
                    
                    matches.append({
                        "line": highlighted_line.strip(),
                        "context": context.strip()
                    })
    except Exception as e:
        print(f"Error reading file {filepath}: {str(e)}")
    return matches

def get_suggestions(filepath: str, query: str) -> List[SuggestionResult]:
    suggestions = []
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            for line in lines:
                if query.lower() in line.lower():
                    # Находим позицию запроса в строке
                    pos = line.lower().find(query.lower())
                    # Берем текст после запроса
                    suggestion_text = line[pos + len(query):].strip()
                    if suggestion_text:
                        suggestions.append(SuggestionResult(
                            text=suggestion_text,
                            filename=os.path.basename(filepath)
                        ))
    except Exception as e:
        print(f"Error reading file {filepath}: {str(e)}")
    return suggestions

def require_web_session(func: Callable):
    @wraps(func)
    async def wrapper(*args, request: Request, **kwargs):
        session_id = request.cookies.get("session_id")
        
        # Проверяем, был ли запрос к главной странице
        if not session_filters.check_url(session_id, "/"):
            raise HTTPException(
                status_code=400,
                detail="Это API доступно только через веб-интерфейс. Пожалуйста, сначала посетите главную страницу."
            )
        
        return await func(*args, request=request, **kwargs)
    return wrapper

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.post("/api/search")
@require_web_session
async def search(query: SearchQuery, request: Request):
    if not query.query.strip():
        raise HTTPException(status_code=400, detail="Поисковый запрос не может быть пустым")
    
    results = []
    data_dir = "data"
    
    for filename in os.listdir(data_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(data_dir, filename)
            matches = search_in_file(filepath, query.query)
            if matches:
                results.append(SearchResult(
                    filename=filename,
                    matches=matches
                ))
    
    return results

@app.post("/api/suggestions")
@require_web_session
async def get_search_suggestions(query: SearchQuery, request: Request):
    if not query.query.strip():
        return []
    
    all_suggestions = []
    data_dir = "data"
    
    for filename in os.listdir(data_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(data_dir, filename)
            suggestions = get_suggestions(filepath, query.query)
            all_suggestions.extend(suggestions)
    
    # Ограничиваем количество подсказок
    return all_suggestions[:5]

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 