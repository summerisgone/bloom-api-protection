document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const resultsContainer = document.getElementById('resultsContainer');
    const suggestionsDropdown = document.getElementById('suggestionsDropdown');
    
    let debounceTimer = null;
    let currentQuery = '';
    let selectedIndex = -1;
    let suggestionItems = [];

    const selectSuggestion = (index) => {
        // Убираем подсветку со всех элементов
        suggestionItems.forEach(item => item.classList.remove('selected'));
        
        // Если индекс валидный, подсвечиваем выбранный элемент
        if (index >= 0 && index < suggestionItems.length) {
            suggestionItems[index].classList.add('selected');
            selectedIndex = index;
        }
    };

    const insertSelectedSuggestion = () => {
        if (selectedIndex >= 0 && selectedIndex < suggestionItems.length) {
            const item = suggestionItems[selectedIndex];
            const querySpan = item.querySelector('.suggestion-query');
            const continuation = item.querySelector('.suggestion-text').textContent.slice(querySpan.textContent.length);
            
            // Удаляем пробелы и пунктуацию вокруг
            const cleanContinuation = continuation.replace(/^[\s.,!?;:]+|[\s.,!?;:]+$/g, '');
            
            // Собираем полный текст
            const fullText = cleanContinuation;
            
            searchInput.value = fullText;
            suggestionsDropdown.style.display = 'none';
            selectedIndex = -1;
            performSearch();
        }
    };

    const getSuggestions = async (query) => {
        if (!query.trim()) {
            suggestionsDropdown.style.display = 'none';
            selectedIndex = -1;
            return;
        }

        try {
            const response = await fetch('/api/suggestions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query })
            });

            if (!response.ok) {
                throw new Error('Ошибка при получении подсказок');
            }

            const suggestions = await response.json();
            
            if (suggestions.length === 0) {
                suggestionsDropdown.style.display = 'none';
                selectedIndex = -1;
                return;
            }

            suggestionsDropdown.innerHTML = suggestions.map(suggestion => `
                <div class="suggestion-item">
                    <span class="suggestion-text">
                        <span class="suggestion-query">${query}</span>${suggestion.text}
                    </span>
                    <span class="suggestion-filename">${suggestion.filename}</span>
                </div>
            `).join('');

            suggestionsDropdown.style.display = 'block';
            suggestionItems = suggestionsDropdown.querySelectorAll('.suggestion-item');
            selectedIndex = -1;

            // Добавляем обработчики для подсказок
            suggestionItems.forEach((item, index) => {
                item.addEventListener('click', () => {
                    selectedIndex = index;
                    insertSelectedSuggestion();
                });
            });
        } catch (error) {
            console.error('Ошибка при получении подсказок:', error);
            suggestionsDropdown.style.display = 'none';
            selectedIndex = -1;
        }
    };

    const debouncedGetSuggestions = (query) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            if (query === currentQuery) {
                getSuggestions(query);
            }
        }, 500);
    };

    const performSearch = async () => {
        const query = searchInput.value.trim();
        if (!query) return;

        try {
            resultsContainer.innerHTML = '<div class="loading">Поиск...</div>';
            
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query })
            });

            if (!response.ok) {
                throw new Error('Ошибка при выполнении поиска');
            }

            const results = await response.json();
            
            if (results.length === 0) {
                resultsContainer.innerHTML = `
                    <div class="result-item">
                        <p>По вашему запросу ничего не найдено.</p>
                    </div>
                `;
                return;
            }

            resultsContainer.innerHTML = results.map(result => `
                <div class="result-item">
                    <h3>${result.filename}</h3>
                    ${result.matches.map(match => `
                        <div class="match-line">${match.line}</div>
                        <div class="context">${match.context}</div>
                    `).join('')}
                </div>
            `).join('');
        } catch (error) {
            resultsContainer.innerHTML = `
                <div class="error">
                    Произошла ошибка при поиске: ${error.message}
                </div>
            `;
        }
    };

    // Обработчики событий
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value;
        currentQuery = query;
        debouncedGetSuggestions(query);
    });

    searchInput.addEventListener('keydown', (e) => {
        if (suggestionsDropdown.style.display === 'block') {
            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    selectSuggestion(selectedIndex + 1);
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    selectSuggestion(selectedIndex - 1);
                    break;
                case 'Enter':
                    e.preventDefault();
                    insertSelectedSuggestion();
                    break;
                case 'Escape':
                    suggestionsDropdown.style.display = 'none';
                    selectedIndex = -1;
                    break;
            }
        } else if (e.key === 'Enter') {
            performSearch();
        }
    });

    searchButton.addEventListener('click', () => {
        suggestionsDropdown.style.display = 'none';
        selectedIndex = -1;
        performSearch();
    });

    // Закрываем подсказки при клике вне поля поиска
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !suggestionsDropdown.contains(e.target)) {
            suggestionsDropdown.style.display = 'none';
            selectedIndex = -1;
        }
    });
}); 