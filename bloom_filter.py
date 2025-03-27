import mmh3
from typing import Dict

class BloomFilter:
    def __init__(self, size: int, hash_count: int):
        self.size = size
        self.hash_count = hash_count
        self.bit_array = [0] * size

    def add(self, item: str):
        for seed in range(self.hash_count):
            index = mmh3.hash(item, seed) % self.size
            self.bit_array[index] = 1

    def check(self, item: str) -> bool:
        for seed in range(self.hash_count):
            index = mmh3.hash(item, seed) % self.size
            if self.bit_array[index] == 0:
                return False
        return True

class SessionBloomFilters:
    def __init__(self, size: int = 1000, hash_count: int = 7):
        self.size = size
        self.hash_count = hash_count
        self.filters: Dict[str, BloomFilter] = {}

    def get_or_create_filter(self, session_id: str) -> BloomFilter:
        if session_id not in self.filters:
            self.filters[session_id] = BloomFilter(self.size, self.hash_count)
        return self.filters[session_id]

    def add_url(self, session_id: str, url: str):
        if session_id:
            self.get_or_create_filter(session_id).add(url)

    def check_url(self, session_id: str, url: str) -> bool:
        if not session_id or session_id not in self.filters:
            return False
        return self.filters[session_id].check(url)

# Создаем глобальный экземпляр для хранения фильтров сессий
session_filters = SessionBloomFilters() 