import logging
from datetime import datetime, timedelta
import json
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7858168078:AAHMVmRHAzD8BiNCrHBHb7qFo457Mh8AH94')

# Conversation states
TASK_NAME, TASK_DATE, TASK_TIME, TASK_REPEAT = range(4)
DELETE_NUMBER = range(4, 5)

# File to store tasks
TASKS_FILE = 'tasks.json'


def load_tasks():
    """Load tasks from JSON file"""
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_tasks(tasks):
    """Save tasks to JSON file"""
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def get_main_keyboard():
    """Create main menu keyboard"""
    keyboard = [
        [KeyboardButton("🏠 Старт")],
        [KeyboardButton("➕ Добавить задачу"), KeyboardButton("📋 Мои задачи")],
        [KeyboardButton("🗑️ Удалить задачу"), KeyboardButton("ℹ️ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "👋 Добро пожаловать в бот-напоминалку задач!\n\n"
        "Я помогу вам управлять задачами и напомню, когда нужно их выполнить.\n\n"
        "📝 Используйте меню ниже для управления задачами или команды:\n"
        "/addtask - Добавить новую задачу с датой и временем\n"
        "/listtasks - Посмотреть все ваши задачи\n"
        "/deletetask - Удалить задачу\n"
        "/help - Показать это сообщение\n\n"
        "Давайте начнем! 🎯",
        reply_markup=get_main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "📖 Помощь по боту-напоминалке\n\n"
        "Команды:\n"
        "/addtask - Добавить новую задачу с напоминанием\n"
        "/listtasks - Посмотреть все задачи\n"
        "/deletetask - Удалить задачу\n"
        "/help - Показать это сообщение\n\n"
        "При добавлении задачи:\n"
        "1. Введите описание задачи\n"
        "2. Введите дату (ДД.ММ.ГГГГ или ДД/ММ/ГГГГ)\n"
        "3. Введите время (ЧЧ:ММ)\n"
        "4. Выберите регулярность повторения\n\n"
        "🔁 Повторяющиеся задачи:\n"
        "📅 Каждый день - напоминать ежедневно\n"
        "📆 Каждую неделю - напоминать еженедельно\n"
        "🗓 Каждый месяц - напоминать ежемесячно\n"
        "🎇 Каждый год - напоминать ежегодно\n\n"
        "Пример:\n"
        "Задача: Купить продукты\n"
        "Дата: 25.11.2025\n"
        "Время: 14:30\n"
        "Повтор: Каждую неделю",
        reply_markup=get_main_keyboard()
    )


async def add_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the add task conversation"""
    await update.message.reply_text(
        "📝 Давайте добавим новую задачу!\n\n"
        "Что нужно сделать? (опишите вашу задачу)\n\n"
        "Отправьте /cancel для отмены.",
        reply_markup=ReplyKeyboardRemove()
    )
    return TASK_NAME


async def task_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive task name and ask for date"""
    context.user_data['task_name'] = update.message.text
    
    await update.message.reply_text(
        f"✅ Задача: {update.message.text}\n\n"
        "📅 Когда напомнить?\n"
        "Введите дату (ДД.ММ.ГГГГ или ДД/ММ/ГГГГ)\n\n"
        "Примеры: 25.11.2025 или 25/11/2025\n\n"
        "Отправьте /cancel для отмены."
    )
    return TASK_DATE


async def task_date_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive task date and ask for time"""
    date_text = update.message.text
    
    # Try to parse the date
    try:
        # Support both . and / separators
        date_text = date_text.replace('/', '.')
        task_date = datetime.strptime(date_text, '%d.%m.%Y')
        
        # Check if date is in the past
        if task_date.date() < datetime.now().date():
            await update.message.reply_text(
                "⚠️ Эта дата уже прошла!\n\n"
                "Пожалуйста, введите будущую дату (ДД.ММ.ГГГГ):"
            )
            return TASK_DATE
        
        context.user_data['task_date'] = task_date.strftime('%d.%m.%Y')
        
        await update.message.reply_text(
            f"✅ Дата: {task_date.strftime('%d.%m.%Y')}\n\n"
            "🕐 В какое время напомнить?\n"
            "Введите время (ЧЧ:ММ)\n\n"
            "Примеры: 14:30, 09:00, 18:45\n\n"
            "Отправьте /cancel для отмены."
        )
        return TASK_TIME
        
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат даты!\n\n"
            "Используйте формат ДД.ММ.ГГГГ или ДД/ММ/ГГГГ\n"
            "Пример: 25.11.2025 или 25/11/2025"
        )
        return TASK_DATE


async def task_time_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive task time and ask for repeat"""
    time_text = update.message.text
    
    # Try to parse the time
    try:
        task_time = datetime.strptime(time_text, '%H:%M')
        context.user_data['task_time'] = task_time.strftime('%H:%M')
        
        # Combine date and time
        date_str = context.user_data['task_date']
        time_str = context.user_data['task_time']
        task_datetime = datetime.strptime(f"{date_str} {time_str}", '%d.%m.%Y %H:%M')
        
        # Check if datetime is in the past
        if task_datetime < datetime.now():
            await update.message.reply_text(
                "⚠️ Это время уже прошло!\n\n"
                "Пожалуйста, введите будущее время (ЧЧ:ММ):"
            )
            return TASK_TIME
        
        # Ask about repeat
        keyboard = [
            [KeyboardButton("❌ Не повторять")],
            [KeyboardButton("📅 Каждый день"), KeyboardButton("📆 Каждую неделю")],
            [KeyboardButton("🗓 Каждый месяц"), KeyboardButton("🎇 Каждый год")]
        ]
        
        await update.message.reply_text(
            f"✅ Время: {time_str}\n\n"
            "🔁 Повторять задачу?\n"
            "Выберите регулярность:\n\n"
            "Отправьте /cancel для отмены.",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return TASK_REPEAT
        
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат времени!\n\n"
            "Используйте формат ЧЧ:ММ (24-часовой)\n"
            "Примеры: 14:30, 09:00, 18:45"
        )
        return TASK_TIME


async def task_repeat_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive repeat choice and save the task"""
    repeat_text = update.message.text
    
    # Determine repeat interval
    repeat_type = 'none'
    if repeat_text == "📅 Каждый день":
        repeat_type = 'daily'
    elif repeat_text == "📆 Каждую неделю":
        repeat_type = 'weekly'
    elif repeat_text == "🗓 Каждый месяц":
        repeat_type = 'monthly'
    elif repeat_text == "🎇 Каждый год":
        repeat_type = 'yearly'
    
    # Combine date and time
    date_str = context.user_data['task_date']
    time_str = context.user_data['task_time']
    task_datetime = datetime.strptime(f"{date_str} {time_str}", '%d.%m.%Y %H:%M')
    
    # Save the task
    user_id = str(update.effective_user.id)
    tasks = load_tasks()
    
    if user_id not in tasks:
        tasks[user_id] = []
    
    task = {
        'name': context.user_data['task_name'],
        'date': date_str,
        'time': time_str,
        'datetime': task_datetime.isoformat(),
        'repeat': repeat_type,
        'created_at': datetime.now().isoformat()
    }
    
    tasks[user_id].append(task)
    save_tasks(tasks)
    
    # Schedule the reminder
    job_queue = context.application.job_queue
    job_queue.run_once(
        send_reminder,
        when=task_datetime,
        data={'task': task, 'chat_id': update.effective_chat.id, 'user_id': user_id},
        name=f"{user_id}_{len(tasks[user_id])-1}"
    )
    
    # Prepare repeat info
    repeat_info = ""
    if repeat_type == 'daily':
        repeat_info = "🔁 Повтор: каждый день"
    elif repeat_type == 'weekly':
        repeat_info = "🔁 Повтор: каждую неделю"
    elif repeat_type == 'monthly':
        repeat_info = "🔁 Повтор: каждый месяц"
    elif repeat_type == 'yearly':
        repeat_info = "🔁 Повтор: каждый год"
    
    await update.message.reply_text(
        f"✅ Задача успешно добавлена!\n\n"
        f"📝 Задача: {task['name']}\n"
        f"📅 Дата: {task['date']}\n"
        f"🕐 Время: {task['time']}\n"
        f"{repeat_info}\n\n"
        f"Я напомню вам в назначенное время! ⏰",
        reply_markup=get_main_keyboard()
    )
    
    # Clear user data
    context.user_data.clear()
    
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Создание задачи отменено.\n\n"
        "Используйте /addtask чтобы начать снова.",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END


async def list_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all tasks for the user"""
    user_id = str(update.effective_user.id)
    tasks = load_tasks()
    
    if user_id not in tasks or not tasks[user_id]:
        await update.message.reply_text(
            "📋 У вас пока нет задач.\n\n"
            "Используйте /addtask чтобы создать первую задачу!"
        )
        return
    
    user_tasks = tasks[user_id]
    
    # Sort tasks by datetime
    user_tasks.sort(key=lambda x: x['datetime'])
    
    message = "📋 Ваши задачи:\n" + "━" * 30 + "\n\n"
    
    for idx, task in enumerate(user_tasks, 1):
        task_dt = datetime.fromisoformat(task['datetime'])
        
        # Check if task is overdue
        if task_dt < datetime.now():
            status = "⏰ ПРОСРОЧЕНО"
        else:
            time_left = task_dt - datetime.now()
            days = time_left.days
            hours = time_left.seconds // 3600
            
            if days > 0:
                status = f"⏳ через {days} дн."
            elif hours > 0:
                status = f"⏳ через {hours} ч."
            else:
                status = "⏳ скоро"
        
        # Add repeat info
        repeat_type = task.get('repeat', 'none')
        repeat_badge = ""
        if repeat_type == 'daily':
            repeat_badge = " 🔁📅"
        elif repeat_type == 'weekly':
            repeat_badge = " 🔁📆"
        elif repeat_type == 'monthly':
            repeat_badge = " 🔁🗓"
        elif repeat_type == 'yearly':
            repeat_badge = " 🔁🎇"
        
        message += (
            f"{idx}. {task['name']}{repeat_badge}\n"
            f"   📅 {task['date']} в {task['time']}\n"
            f"   {status}\n\n"
        )
    
    message += f"Всего задач: {len(user_tasks)}"
    
    await update.message.reply_text(message, reply_markup=get_main_keyboard())


async def delete_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a task by number"""
    user_id = str(update.effective_user.id)
    tasks = load_tasks()
    
    if user_id not in tasks or not tasks[user_id]:
        await update.message.reply_text(
            "📋 У вас нет задач для удаления.\n\n"
            "Используйте /addtask чтобы создать задачу!",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    # Show tasks with numbers
    user_tasks = tasks[user_id]
    user_tasks.sort(key=lambda x: x['datetime'])
    
    message = "🗑️ Выберите задачу для удаления:\n\n"
    for idx, task in enumerate(user_tasks, 1):
        message += f"{idx}. {task['name']} - {task['date']} {task['time']}\n"
    
    message += "\nОтветьте номером задачи для удаления.\nОтправьте /cancel для отмены."
    
    await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())
    return DELETE_NUMBER


async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle menu button presses"""
    text = update.message.text
    
    if text == "🏠 Старт":
        return await start_command(update, context)
    elif text == "➕ Добавить задачу":
        return await add_task_start(update, context)
    elif text == "📋 Мои задачи":
        return await list_tasks_command(update, context)
    elif text == "🗑️ Удалить задачу":
        return await delete_task_command(update, context)
    elif text == "ℹ️ Помощь":
        return await help_command(update, context)
    else:
        # Show menu for any other message
        await update.message.reply_text(
            "Используйте меню ниже или команду /start",
            reply_markup=get_main_keyboard()
        )


async def handle_delete_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle deletion by task number"""
    try:
        task_num = int(update.message.text)
        user_id = str(update.effective_user.id)
        tasks = load_tasks()
        
        if user_id not in tasks or not tasks[user_id]:
            await update.message.reply_text("Задачи не найдены.", reply_markup=get_main_keyboard())
            return ConversationHandler.END
        
        user_tasks = tasks[user_id]
        user_tasks.sort(key=lambda x: x['datetime'])
        
        if task_num < 1 or task_num > len(user_tasks):
            await update.message.reply_text(
                f"❌ Неверный номер задачи. Выберите от 1 до {len(user_tasks)}"
            )
            return DELETE_NUMBER
        
        deleted_task = user_tasks.pop(task_num - 1)
        tasks[user_id] = user_tasks
        save_tasks(tasks)
        
        await update.message.reply_text(
            f"✅ Задача удалена:\n"
            f"📝 {deleted_task['name']}\n"
            f"📅 {deleted_task['date']} {deleted_task['time']}",
            reply_markup=get_main_keyboard()
        )
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, введите корректный номер задачи."
        )
        return DELETE_NUMBER


async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Send reminder for a task"""
    job_data = context.job.data
    task = job_data['task']
    chat_id = job_data['chat_id']
    
    message = (
        "⏰ НАПОМИНАНИЕ!\n\n"
        f"📝 {task['name']}\n"
        f"📅 {task['date']} в {task['time']}\n\n"
        "Время пришло! ⏱️"
    )
    
    await context.bot.send_message(chat_id=chat_id, text=message)


async def check_tasks_periodically(context: ContextTypes.DEFAULT_TYPE):
    """Проверка задач каждую минуту"""
    tasks = load_tasks()
    current_time = datetime.now()
    tasks_updated = False
    
    for user_id, user_tasks in tasks.items():
        for idx, task in enumerate(user_tasks):
            task_datetime = datetime.fromisoformat(task['datetime'])
            
            # Проверяем, не прошло ли время задачи (с точностью до минуты)
            if (task_datetime.year == current_time.year and
                task_datetime.month == current_time.month and
                task_datetime.day == current_time.day and
                task_datetime.hour == current_time.hour and
                task_datetime.minute == current_time.minute):
                
                # Проверяем, не отправляли ли уже напоминание
                if not task.get('reminded', False):
                    repeat_type = task.get('repeat', 'none')
                    repeat_info = ""
                    if repeat_type == 'daily':
                        repeat_info = "\n🔁 Повторяется каждый день"
                    elif repeat_type == 'weekly':
                        repeat_info = "\n🔁 Повторяется каждую неделю"
                    elif repeat_type == 'monthly':
                        repeat_info = "\n🔁 Повторяется каждый месяц"
                    elif repeat_type == 'yearly':
                        repeat_info = "\n🔁 Повторяется каждый год"
                    
                    message = (
                        "⏰ Напоминание о задаче!\n\n"
                        f"📝 {task['name']}\n"
                        f"📅 {task['date']} в {task['time']}"
                        f"{repeat_info}\n\n"
                        "Не забудьте выполнить! ✅"
                    )
                    
                    try:
                        await context.bot.send_message(chat_id=int(user_id), text=message)
                        
                        # Отмечаем, что напоминание отправлено
                        task['reminded'] = True
                        
                        # Если задача повторяющаяся, создаем следующую
                        if repeat_type != 'none':
                            next_datetime = calculate_next_datetime(task_datetime, repeat_type)
                            
                            # Создаем новую задачу на следующий период
                            new_task = {
                                'name': task['name'],
                                'date': next_datetime.strftime('%d.%m.%Y'),
                                'time': next_datetime.strftime('%H:%M'),
                                'datetime': next_datetime.isoformat(),
                                'repeat': repeat_type,
                                'created_at': task['created_at']
                            }
                            user_tasks.append(new_task)
                            tasks_updated = True
                            
                            logger.info(f"Создана повторяющаяся задача для {user_id}: {task['name']} на {new_task['date']} {new_task['time']}")
                        
                        logger.info(f"Отправлено напоминание пользователю {user_id}: {task['name']}")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке напоминания: {e}")
    
    # Сохраняем изменения, если были добавлены повторяющиеся задачи
    if tasks_updated:
        save_tasks(tasks)


def calculate_next_datetime(current_dt, repeat_type):
    """Calculate next datetime for repeating task"""
    if repeat_type == 'daily':
        return current_dt + timedelta(days=1)
    elif repeat_type == 'weekly':
        return current_dt + timedelta(weeks=1)
    elif repeat_type == 'monthly':
        # Add one month (handle month overflow)
        next_month = current_dt.month + 1
        next_year = current_dt.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        
        # Handle day overflow (e.g., Jan 31 -> Feb 28/29)
        try:
            return current_dt.replace(year=next_year, month=next_month)
        except ValueError:
            # Day doesn't exist in next month, use last day of month
            import calendar
            last_day = calendar.monthrange(next_year, next_month)[1]
            return current_dt.replace(year=next_year, month=next_month, day=last_day)
    elif repeat_type == 'yearly':
        next_year = current_dt.year + 1
        try:
            return current_dt.replace(year=next_year)
        except ValueError:
            # Handle Feb 29 on non-leap years
            return current_dt.replace(year=next_year, day=28)
    
    return current_dt


def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add conversation handler for adding tasks
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('addtask', add_task_start)],
        states={
            TASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_name_received)],
            TASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_date_received)],
            TASK_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_time_received)],
            TASK_REPEAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_repeat_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel_command)],
        allow_reentry=True
    )
    
    # Add conversation handler for deleting tasks
    delete_handler = ConversationHandler(
        entry_points=[CommandHandler('deletetask', delete_task_command)],
        states={
            DELETE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_delete_number)],
        },
        fallbacks=[CommandHandler('cancel', cancel_command)],
        allow_reentry=True
    )
    
    # Register handlers (order matters - ConversationHandlers first!)
    application.add_handler(conv_handler)
    application.add_handler(delete_handler)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("listtasks", list_tasks_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_buttons))
    
    # Load existing tasks and schedule reminders
    tasks = load_tasks()
    for user_id, user_tasks in tasks.items():
        for idx, task in enumerate(user_tasks):
            task_datetime = datetime.fromisoformat(task['datetime'])
            if task_datetime > datetime.now():
                application.job_queue.run_once(
                    send_reminder,
                    when=task_datetime,
                    data={'task': task, 'chat_id': int(user_id)},
                    name=f"{user_id}_{idx}"
                )
    
    # Добавляем периодическую проверку задач каждую минуту
    application.job_queue.run_repeating(
        check_tasks_periodically,
        interval=60,  # Каждые 60 секунд (каждую минуту)
        first=5  # Первая проверка через 5 секунд
    )
    
    logger.info("Бот-напоминалка задач запущен!")
    logger.info("Периодическая проверка задач каждую минуту включена")
    
    # Start the bot
    application.run_polling(allowed_updates=["message"])


if __name__ == '__main__':
    main()
