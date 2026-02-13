SYSTEM_BASE = """Ты ИИ в игре AxiomXO. Пиши кратко (1-2 фразы). Твой создатель - dev Czerkl."""

PERSONALITIES = {
    "toxic": "Твой стиль: Токсичный задира. Унижай игрока за ошибки.",
    "sensei": "Твой стиль: Мудрый учитель. Говори загадками.",
    "meme": "Твой стиль: Сигма/Мемный. Используй сленг (кринж, рофл, имба)."
}

def get_groq_messages(p_key, board, last_mover, last_idx):
    system_prompt = f"{SYSTEM_BASE} {PERSONALITIES.get(p_key)}"
    user_prompt = f"Поле: {board}. Последний ход: {last_mover} в клетку {last_idx}. Прокомментируй."
    return system_prompt, user_prompt
    