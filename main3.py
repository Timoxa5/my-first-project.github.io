import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import random
from config import API_TOKEN


logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class GoalState(StatesGroup):
    goal = State()

user_goals = {}

def random_message(messages):
    return random.choice(messages)

@dp.message_handler(commands='start')
async def send_welcome(message: types.Message):
    user_name = message.from_user.first_name or "друг"
    greetings = [
        f"Привет, {user_name}! Я здесь, чтобы помочь тебе следить за твоими целями на сегодня ",
        f"Здравствуй, {user_name}! Давай вместе работать над твоими целями ",
        f"Приветствую, {user_name}! Готов поддерживать тебя с твоими задачами "
    ]
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Добавить цели", callback_data="set_goal"))
    keyboard.add(InlineKeyboardButton("Посмотреть цели", callback_data="view_goals"))
    await message.answer(random_message(greetings), reply_markup=keyboard)

@dp.message_handler(commands='my_id')
async def send_user_id(message: types.Message):
    user_id = message.from_user.id
    await message.answer(f"Твой ID: {user_id}")

async def handle_set_goal(call: types.CallbackQuery):
    await call.message.answer("Напиши свои цели на сегодня, просто перечисли их через новую строку. Не стесняйся! ")
    await GoalState.goal.set()

@dp.callback_query_handler(text='set_goal')
async def set_goal_callback(call: types.CallbackQuery):
    await handle_set_goal(call)

@dp.message_handler(state=GoalState.goal)
async def process_goal(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    goals = message.text.split('\n')
    user_goals[user_id] = {'goals': goals, 'completed': [False] * len(goals)}

    await state.finish()

    responses = [
        "Отлично, все цели записаны! ",
        "Записал! Вперед к достижениям! ",
        "Готово! Я запомнил, и теперь они у меня под контролем "
    ]
    await message.answer(random_message(responses))

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Посмотреть цели", callback_data="view_goals"))

    follow_up = [
        "Что дальше будем делать? ",
        "Выбирай следующее действие!",
        "Чем займемся дальше?"
    ]
    await message.answer(random_message(follow_up), reply_markup=keyboard)

async def handle_view_goals(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in user_goals or not user_goals[user_id]['goals']:
        await call.message.answer("Пока целей нет. Может, добавим парочку? ")
    else:
        keyboard = InlineKeyboardMarkup()
        for i, goal in enumerate(user_goals[user_id]['goals']):
            button_text = f" {goal}" if user_goals[user_id]['completed'][i] else f" {goal}"
            keyboard.add(InlineKeyboardButton(button_text, callback_data=f"goal_{i}"))
        await call.message.answer("Вот твои цели на сегодня:", reply_markup=keyboard)

@dp.callback_query_handler(text='view_goals')
async def view_goals_callback(call: types.CallbackQuery):
    await handle_view_goals(call)

async def handle_mark_goal(call: types.CallbackQuery):
    user_id = call.from_user.id
    goal_index = int(call.data.split('_')[1])
    user_goals[user_id]['completed'][goal_index] = not user_goals[user_id]['completed'][goal_index]
    status = "выполненной" if user_goals[user_id]['completed'][goal_index] else "невыполненной"

    await call.answer(f"Цель отмечена как {status}. ")

    keyboard = InlineKeyboardMarkup()
    for i, goal in enumerate(user_goals[user_id]['goals']):
        button_text = f" {goal}" if user_goals[user_id]['completed'][i] else f" {goal}"
        keyboard.add(InlineKeyboardButton(button_text, callback_data=f"goal_{i}"))

    await call.message.edit_reply_markup(reply_markup=keyboard)

@dp.callback_query_handler(lambda call: call.data.startswith("goal_"))
async def mark_goal_callback(call: types.CallbackQuery):
    await handle_mark_goal(call)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
