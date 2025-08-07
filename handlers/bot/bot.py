import asyncio
import json
import logging
import os
from typing import Callable, Dict, Any, Awaitable
from aiogram import Bot, Dispatcher, types, BaseMiddleware
from aiogram.filters.command import Command
from aiogram.types import Update, TelegramObject
from bot_handlers import BotHandlers

token = os.getenv("TELEGRAM_BOT_TOKEN")
if token is None:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

# Получаем список ID администраторов
admin_user_ids_str = os.getenv("ADMIN_USER_ID")
if admin_user_ids_str is None:
    raise ValueError("ADMIN_USER_ID environment variable is not set")

# Парсим ID администраторов (поддерживаем два формата: JSON список или строка через запятую)
try:
    # Пытаемся сначала распарсить как JSON
    if admin_user_ids_str.strip().startswith('['):
        admin_user_ids = json.loads(admin_user_ids_str)
        # Преобразуем строки в числа, если нужно
        admin_user_ids = [int(uid) if isinstance(uid, str) else uid for uid in admin_user_ids]
    else:
        # Иначе парсим как строку через запятую
        admin_user_ids = [int(uid.strip()) for uid in admin_user_ids_str.split(',')]
except (ValueError, json.JSONDecodeError) as e:
    raise ValueError(f"ADMIN_USER_ID must contain valid integers in JSON array format or comma-separated: {e}")

def check_admin_access(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return user_id in admin_user_ids

class AdminMiddleware(BaseMiddleware):
    """Middleware для проверки прав администратора"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        username = None
        
        # Получаем user_id из разных типов событий
        if isinstance(event, types.Message) and event.from_user:
            user_id = event.from_user.id
            username = event.from_user.username or event.from_user.first_name
        elif isinstance(event, types.CallbackQuery) and event.from_user:
            user_id = event.from_user.id
            username = event.from_user.username or event.from_user.first_name
        
        if user_id is None or not check_admin_access(user_id):
            # Логируем попытку несанкционированного доступа
            logging.warning(f"Unauthorized access attempt from user_id: {user_id}, username: {username}")
            
            # Если это сообщение, отвечаем пользователю
            if isinstance(event, types.Message):
                await event.answer("❌ У вас нет доступа к этому боту.")
            # Если это callback, отвечаем на него
            elif isinstance(event, types.CallbackQuery):
                await event.answer("❌ У вас нет доступа к этому боту.", show_alert=True)
            return
        
        # Логируем успешный доступ админа
        logging.info(f"Admin access granted for user_id: {user_id}, username: {username}")
        
        # Если пользователь админ, передаем управление дальше
        return await handler(event, data)

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Логируем информацию о настроенных администраторах
logging.info(f"Bot configured with {len(admin_user_ids)} admin(s): {admin_user_ids}")

# Объект бота
bot = Bot(token=token)
# Диспетчер
dp = Dispatcher()

# Регистрируем middleware для проверки прав доступа
admin_middleware = AdminMiddleware()
dp.message.middleware(admin_middleware)
dp.callback_query.middleware(admin_middleware)

# Создаем экземпляр обработчиков
handlers = BotHandlers(bot)

# Регистрируем обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await handlers.handle_start(message)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await handlers.handle_help(message)

# Регистрируем обработчики кнопок
@dp.message(lambda message: message.text == "Управление пользователями")
async def process_manage_users(message: types.Message):
    await handlers.handle_manage_users(message)

@dp.message(lambda message: message.text == "Управление нодами")
async def process_manage_nodes(message: types.Message):
    await handlers.handle_manage_nodes(message)

@dp.message(lambda message: message.text == "Статистика системы")
async def process_system_stats(message: types.Message):
    await handlers.handle_system_stats(message)

@dp.message(lambda message: message.text == "🔙 Назад")
async def process_back(message: types.Message):
    await handlers.handle_back(message)

@dp.message(lambda message: message.text == "🟢 Включить ноду")
async def process_enable_node(message: types.Message):
    await handlers.handle_enable_node(message)

@dp.message(lambda message: message.text == "🔴 Отключить ноду")
async def process_disable_node(message: types.Message):
    await handlers.handle_disable_node(message)

@dp.message(lambda message: message.text == "🔄 Перезагрузить ноду")
async def process_restart_node(message: types.Message):
    await handlers.handle_restart_node(message)

@dp.message(lambda message: message.text == "🔍 Обновить информацию")
async def process_refresh_node_info(message: types.Message):
    await handlers.handle_refresh_node_info(message)

@dp.message(lambda message: message.text == "🔙 Назад к списку нод")
async def process_back_to_nodes(message: types.Message):
    await handlers.handle_back_to_nodes(message)

@dp.message(lambda message: message.text == "🔄 Перезагрузить все ноды")
async def process_restart_all_nodes(message: types.Message):
    await handlers.handle_restart_all_nodes(message)

# Обработчик для выбора конкретной ноды (должен быть последним)
@dp.message(lambda message: message.text and handlers.is_node_name(message.text))
async def process_node_selection(message: types.Message):
    await handlers.handle_node_selection(message)

# Обработчик для текстового ввода при создании пользователя
@dp.message(lambda message: message.text and handlers.is_waiting_for_user_input())
async def process_user_text_input(message: types.Message):
    await handlers.handle_user_text_input(message)

# Обработчики для инлайн-кнопок
@dp.callback_query(lambda c: c.data == "enable_node")
async def process_inline_enable_node(callback_query: types.CallbackQuery):
    await handlers.handle_inline_enable_node(callback_query)

@dp.callback_query(lambda c: c.data == "disable_node")
async def process_inline_disable_node(callback_query: types.CallbackQuery):
    await handlers.handle_inline_disable_node(callback_query)

@dp.callback_query(lambda c: c.data == "restart_node")
async def process_inline_restart_node(callback_query: types.CallbackQuery):
    await handlers.handle_inline_restart_node(callback_query)

@dp.callback_query(lambda c: c.data == "refresh_info")
async def process_inline_refresh_info(callback_query: types.CallbackQuery):
    await handlers.handle_inline_refresh_info(callback_query)

@dp.callback_query(lambda c: c.data == "back_to_nodes")
async def process_inline_back_to_nodes(callback_query: types.CallbackQuery):
    await handlers.handle_inline_back_to_nodes(callback_query)

@dp.callback_query(lambda c: c.data == "confirm_restart_all")
async def process_confirm_restart_all(callback_query: types.CallbackQuery):
    await handlers.handle_confirm_restart_all(callback_query)

@dp.callback_query(lambda c: c.data == "cancel_restart_all")
async def process_cancel_restart_all(callback_query: types.CallbackQuery):
    await handlers.handle_cancel_restart_all(callback_query)

# Обработчики пагинации пользователей
@dp.callback_query(lambda c: c.data == "users_next_page")
async def process_users_next_page(callback_query: types.CallbackQuery):
    await handlers.handle_users_pagination(callback_query, "next")

@dp.callback_query(lambda c: c.data == "users_prev_page")
async def process_users_prev_page(callback_query: types.CallbackQuery):
    await handlers.handle_users_pagination(callback_query, "prev")

# Обработчик выбора пользователя
@dp.callback_query(lambda c: c.data and c.data.startswith("user_select_"))
async def process_user_select(callback_query: types.CallbackQuery):
    logging.info(f"Получен callback для выбора пользователя: {callback_query.data}")
    
    if not callback_query.data:
        await callback_query.answer("❌ Ошибка обработки", show_alert=True)
        return
    
    # Извлекаем UUID из callback_data
    user_uuid = callback_query.data.replace("user_select_", "")
    logging.info(f"Извлеченный UUID пользователя: {user_uuid}")
    
    await handlers.handle_user_select_by_uuid(callback_query, user_uuid)

# Обработчики управления пользователями
@dp.callback_query(lambda c: c.data == "refresh_users")
async def process_refresh_users(callback_query: types.CallbackQuery):
    await handlers.handle_refresh_users(callback_query)

@dp.callback_query(lambda c: c.data == "create_user_menu")
async def process_create_user_menu(callback_query: types.CallbackQuery):
    await handlers.handle_create_user_menu(callback_query)

@dp.callback_query(lambda c: c.data == "quick_create_user")
async def process_quick_create_user(callback_query: types.CallbackQuery):
    await handlers.handle_quick_create_user(callback_query)

@dp.callback_query(lambda c: c.data == "create_user_quick")
async def process_create_user_quick_alt(callback_query: types.CallbackQuery):
    await handlers.handle_quick_create_user(callback_query)

@dp.callback_query(lambda c: c.data == "create_user_custom")
async def process_create_user_custom(callback_query: types.CallbackQuery):
    await handlers.handle_create_user_custom(callback_query)

# Обработчики выбора сквада
@dp.callback_query(lambda c: c.data and c.data.startswith("select_squad_"))
async def process_squad_selection(callback_query: types.CallbackQuery):
    if not callback_query.data:
        return
    squad_uuid = callback_query.data.split("_", 2)[-1]  # получаем UUID после "select_squad_"
    await handlers.handle_squad_selection(callback_query, squad_uuid)

@dp.callback_query(lambda c: c.data == "proceed_to_squad_selection")
async def process_proceed_to_squad_selection(callback_query: types.CallbackQuery):
    await handlers.handle_proceed_to_squad_selection(callback_query)

# Обработчики для настройки пользовательского создания
@dp.callback_query(lambda c: c.data == "set_username")
async def process_set_username(callback_query: types.CallbackQuery):
    await callback_query.answer()
    handlers.user_manager.waiting_for_username = True
    if callback_query.message:
        await callback_query.message.answer("Введите имя пользователя:")

@dp.callback_query(lambda c: c.data == "set_expire_days")
async def process_set_expire_days(callback_query: types.CallbackQuery):
    await callback_query.answer()
    handlers.user_manager.waiting_for_expire_days = True
    if callback_query.message:
        await callback_query.message.answer("Введите количество дней действия пользователя:")

@dp.callback_query(lambda c: c.data == "set_traffic_limit")
async def process_set_traffic_limit(callback_query: types.CallbackQuery):
    await callback_query.answer()
    handlers.user_manager.waiting_for_traffic_limit = True
    if callback_query.message:
        await callback_query.message.answer("Введите лимит трафика в GB (или 0 для безлимита):")

@dp.callback_query(lambda c: c.data == "set_description")
async def process_set_description(callback_query: types.CallbackQuery):
    await callback_query.answer()
    handlers.user_manager.waiting_for_description = True
    if callback_query.message:
        await callback_query.message.answer("Введите описание пользователя:")

@dp.callback_query(lambda c: c.data == "set_email")
async def process_set_email(callback_query: types.CallbackQuery):
    await callback_query.answer()
    handlers.user_manager.waiting_for_email = True
    if callback_query.message:
        await callback_query.message.answer("Введите email пользователя:")

@dp.callback_query(lambda c: c.data == "set_tag")
async def process_set_tag(callback_query: types.CallbackQuery):
    await callback_query.answer()
    handlers.user_manager.waiting_for_tag = True
    if callback_query.message:
        await callback_query.message.answer("Введите тег пользователя:")

# Обработчики действий с пользователем
@dp.callback_query(lambda c: c.data == "toggle_user_status")
async def process_toggle_user_status(callback_query: types.CallbackQuery):
    user_data = handlers.user_manager.get_selected_user()
    if user_data:
        await handlers.handle_toggle_user_status(callback_query, user_data)
    else:
        await callback_query.answer("❌ Пользователь не найден", show_alert=True)

@dp.callback_query(lambda c: c.data == "reset_user_traffic")
async def process_reset_user_traffic(callback_query: types.CallbackQuery):
    user_data = handlers.user_manager.get_selected_user()
    if user_data:
        await handlers.handle_reset_user_traffic(callback_query, user_data)
    else:
        await callback_query.answer("❌ Пользователь не найден", show_alert=True)

@dp.callback_query(lambda c: c.data == "get_user_link")
async def process_get_user_link(callback_query: types.CallbackQuery):
    user_data = handlers.user_manager.get_selected_user()
    if user_data:
        await handlers.handle_get_user_link(callback_query, user_data)
    else:
        await callback_query.answer("❌ Пользователь не найден", show_alert=True)

@dp.callback_query(lambda c: c.data == "delete_user")
async def process_delete_user(callback_query: types.CallbackQuery):
    user_data = handlers.user_manager.get_selected_user()
    if user_data:
        await handlers.handle_delete_user(callback_query, user_data)
    else:
        await callback_query.answer("❌ Пользователь не найден", show_alert=True)

@dp.callback_query(lambda c: c.data == "refresh_user_info")
async def process_refresh_user_info(callback_query: types.CallbackQuery):
    user_data = handlers.user_manager.get_selected_user()
    if user_data:
        await handlers.handle_refresh_user_info(callback_query, user_data)
    else:
        await callback_query.answer("❌ Пользователь не найден", show_alert=True)

# Обработчики навигации
@dp.callback_query(lambda c: c.data == "back_to_users")
async def process_back_to_users(callback_query: types.CallbackQuery):
    await handlers.handle_back_to_users(callback_query)

@dp.callback_query(lambda c: c.data == "back_to_main")
async def process_back_to_main(callback_query: types.CallbackQuery):
    await handlers.handle_back_to_main(callback_query)

@dp.callback_query(lambda c: c.data == "cancel_user_creation")
async def process_cancel_user_creation(callback_query: types.CallbackQuery):
    await handlers.handle_cancel_user_creation(callback_query)

# Обработчики статистики системы
@dp.callback_query(lambda c: c.data and c.data.startswith("stats_"))
async def process_stats_category(callback_query: types.CallbackQuery):
    if not callback_query.data:
        await callback_query.answer("❌ Ошибка: нет данных")
        return
        
    if callback_query.data == "stats_refresh_all":
        await handlers.handle_refresh_stats(callback_query)
    elif callback_query.data == "stats_back_to_categories":
        await handlers.handle_stats_back_to_categories(callback_query)
    else:
        await handlers.handle_stats_category(callback_query, callback_query.data)

@dp.callback_query(lambda c: c.data and c.data.startswith("refresh_stats_"))
async def process_refresh_specific_stats(callback_query: types.CallbackQuery):
    if not callback_query.data:
        await callback_query.answer("❌ Ошибка: нет данных")
        return
        
    category = callback_query.data.replace("refresh_", "")
    await handlers.handle_refresh_stats(callback_query, category)

@dp.callback_query(lambda c: c.data and (c.data.startswith("system_") or c.data.startswith("bandwidth_") or c.data.startswith("nodes_")))
async def process_stats_subcategory(callback_query: types.CallbackQuery):
    if not callback_query.data:
        await callback_query.answer("❌ Ошибка: нет данных")
        return
        
    await handlers.handle_stats_subcategory(callback_query, callback_query.data)

# Обработчик для игнорирования кликов по информационным кнопкам
@dp.callback_query(lambda c: c.data == "page_info")
async def process_page_info(callback_query: types.CallbackQuery):
    await callback_query.answer()

# Универсальный обработчик для отладки необработанных callback
@dp.callback_query()
async def catch_all_callback(callback_query: types.CallbackQuery):
    logging.warning(f"Необработанный callback: {callback_query.data} от пользователя {callback_query.from_user.id}")
    await callback_query.answer("⚠️ Неизвестная команда")

# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())