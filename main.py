from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from typing import List, Dict
import re

app = FastAPI(
    title="Bloom Server",
    description="FastAPI server for Bloom application",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене замените на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

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

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.post("/api/search")
async def search(query: SearchQuery):
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
async def get_search_suggestions(query: SearchQuery):
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