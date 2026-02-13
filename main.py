import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from groq import AsyncGroq # Теперь используем Groq
from dotenv import load_dotenv

import engine
import prompts

load_dotenv()
logging.basicConfig(level=logging.INFO)

# Ключи доступа
TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")

# Инициализация Groq
client = AsyncGroq(api_key=GROQ_KEY)

# Глобальный конфиг v2.6
GLOBAL_CONFIG = {
    "model": "llama-3.3-70b-versatile" # Топовая модель для Groq
}

bot = Bot(token=TOKEN)
dp = Dispatcher()
user_games = {}

# --- КЛАВИАТУРЫ ---

def get_settings_keyboard(user_id):
    game = user_games.get(user_id)
    builder = InlineKeyboardBuilder()
    
    # Секция сложности
    diffs = [("Easy", "easy"), ("Medium", "medium"), ("Hard", "hard")]
    for label, code in diffs:
        is_active = " ✅" if game["difficulty"] == code else ""
        builder.button(text=f"{label}{is_active}", callback_data=f"set_diff_{code}")
    
    # Секция личностей (Новинка v2.6!)
    builder.row(types.InlineKeyboardButton(text="🎭 Сменить характер:", callback_data="none"))
    personalities = [("Toxic", "toxic"), ("Sensei", "sensei"), ("Meme", "meme")]
    for label, code in personalities:
        is_active = " ⚡" if game["personality"] == code else ""
        builder.button(text=f"{label}{is_active}", callback_data=f"set_pers_{code}")
        
    builder.adjust(3, 1, 3)
    builder.row(types.InlineKeyboardButton(text="🔙 Назад к игре", callback_data="back_to_game"))
    return builder.as_markup()

def get_board_keyboard(board, game_over=False):
    builder = InlineKeyboardBuilder()
    for i, cell in enumerate(board):
        text = "⬜" if cell == engine.EMPTY else ("❌" if cell == engine.USER else "⭕")
        cb_data = f"cell_{i}" if cell == engine.EMPTY and not game_over else "ignore"
        builder.button(text=text, callback_data=cb_data)
    
    builder.adjust(3)
    if game_over:
        builder.row(types.InlineKeyboardButton(text="🔄 Реванш", callback_data="restart"))
    else:
        builder.row(types.InlineKeyboardButton(text="⚙️ Настройки", callback_data="open_settings"))
    return builder.as_markup()

# --- КОМАНДЫ ---

@dp.message(Command("start"))
async def start_game(message: types.Message):
    user_id = message.from_user.id
    user_games[user_id] = {
        "board": [engine.EMPTY] * 9,
        "difficulty": "hard",
        "personality": "toxic",
        "is_processing": False
    }
    
    await message.answer(
        f"🌌 **AxiomXO v2.6** | dev. Czerkl\n"
        f"Модель: `{GLOBAL_CONFIG['model']}`\n\n"
        "Я готов. Твой ход!",
        reply_markup=get_board_keyboard(user_games[user_id]["board"]),
        parse_mode="Markdown"
    )

@dp.message(Command("change"))
async def change_model(message: types.Message, command: CommandObject):
    """Глобальная смена модели по команде /change [название]"""
    if not command.args:
        return await message.answer("Пример: `/change llama-3.1-8b-instant`", parse_mode="Markdown")
    
    new_model = command.args.strip()
    GLOBAL_CONFIG["model"] = new_model
    await message.answer(f"✅ Модель обновлена для всех на: `{new_model}`", parse_mode="Markdown")

# --- CALLBACKS ---

@dp.callback_query(F.data.startswith("set_pers_"))
async def set_personality(callback: types.CallbackQuery):
    pers = callback.data.split("_")[2]
    user_games[callback.from_user.id]["personality"] = pers
    await callback.message.edit_reply_markup(reply_markup=get_settings_keyboard(callback.from_user.id))
    await callback.answer(f"Характер: {pers.capitalize()}")

@dp.callback_query(F.data.startswith("cell_"))
async def handle_click(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    game = user_games.get(user_id)
    if not game or game["is_processing"]: return await callback.answer()

    index = int(callback.data.split("_")[1])
    game["is_processing"] = True
    game["board"][index] = engine.USER
    
    winner = engine.check_winner(game["board"])
    if not winner:
        move = engine.get_best_move(game["board"], game["difficulty"])
        if move is not None:
            game["board"][move] = engine.BOT
            winner = engine.check_winner(game["board"])
            last_m, last_idx = "Бот", move
        else: winner, last_m, last_idx = 'tie', "Игрок", index
    else: last_m, last_idx = "Игрок", index

    # Формируем промпт для Groq
    board_str = " | ".join([" ".join(game["board"][i:i+3]) for i in range(0, 9, 3)])
    system_p, user_p = prompts.get_groq_messages(game["personality"], board_str, last_m, last_idx)
    
    try:
        # Ультра-быстрый вызов Groq
        completion = await client.chat.completions.create(
            model=GLOBAL_CONFIG["model"],
            messages=[
                {"role": "system", "content": system_p},
                {"role": "user", "content": user_p}
            ],
            max_tokens=60
        )
        comment = completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Groq Error: {e}")
        comment = "Твой ход заставил мои цепи искриться."

    is_over = winner is not None
    status = f"🤖: {comment}"
    if winner == engine.USER: status = "🎉 Победа! Czerkl не поверит..."
    elif winner == engine.BOT: status = f"💀 Поражение.\n\n🤖: {comment}"
    elif winner == 'tie': status = "⚖️ Ничья."

    await callback.message.edit_text(status, reply_markup=get_board_keyboard(game["board"], is_over))
    if is_over: del user_games[user_id]
    else: game["is_processing"] = False

# (Остальные хендлеры настроек и старта из v2.5 остаются аналогичными)
@dp.callback_query(F.data == "open_settings")
async def open_settings(callback: types.CallbackQuery):
    await callback.message.edit_text("⚙️ Настройки AxiomXO:", reply_markup=get_settings_keyboard(callback.from_user.id))

@dp.callback_query(F.data == "back_to_game")
async def back_to_game(callback: types.CallbackQuery):
    await callback.message.edit_text("Игра возобновлена!", reply_markup=get_board_keyboard(user_games[callback.from_user.id]["board"]))

@dp.callback_query(F.data.startswith("set_diff_"))
async def set_diff(callback: types.CallbackQuery):
    user_games[callback.from_user.id]["difficulty"] = callback.data.split("_")[2]
    await callback.message.edit_reply_markup(reply_markup=get_settings_keyboard(callback.from_user.id))

@dp.callback_query(F.data == "restart")
async def restart(callback: types.CallbackQuery):
    await start_game(callback.message)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    