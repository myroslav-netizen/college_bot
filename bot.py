import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from config import BOT_TOKEN
from data.schedule import SCHEDULE
from data.events import EVENTS
from data.faq import FAQ

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# меню

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Розклад занять", callback_data="menu_schedule")],
        [InlineKeyboardButton("🎉 Найближчі події",  callback_data="menu_events")],
        [InlineKeyboardButton("❓ Поширені питання", callback_data="menu_faq")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Привіт! Я інформаційний бот коледжу.\n\n"
        "Оберіть розділ, який вас цікавить:"
    )
    await update.message.reply_text(text, reply_markup=main_menu_keyboard())


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Оберіть розділ, що вас цікавить:",
        reply_markup=main_menu_keyboard()
    )


# розклад

def schedule_groups_keyboard():
    groups = list(SCHEDULE.keys())
    buttons = [[InlineKeyboardButton(g, callback_data=f"group_{g}")] for g in groups]
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)


def schedule_days_keyboard(group: str):
    days = list(SCHEDULE[group].keys())
    buttons = [[InlineKeyboardButton(d, callback_data=f"day_{group}_{d}")] for d in days]
    buttons.append([InlineKeyboardButton("◀️ До груп", callback_data="menu_schedule")])
    return InlineKeyboardMarkup(buttons)


async def menu_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📅 *Розклад занять*\n\nОберіть групу:",
        parse_mode="Markdown",
        reply_markup=schedule_groups_keyboard()
    )


async def show_group_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    group = query.data.replace("group_", "")
    await query.edit_message_text(
        f"📅 Розклад для групи *{group}*\n\nОберіть день тижня:",
        parse_mode="Markdown",
        reply_markup=schedule_days_keyboard(group)
    )


async def show_day_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_", 2)   
    group = parts[1]
    day   = parts[2]
    lessons = SCHEDULE.get(group, {}).get(day, [])

    if lessons:
        lines = [f"📅 *{group} — {day}*\n"]
        for i, lesson in enumerate(lessons, 1):
            lines.append(
                f"*{i}. {lesson['time']}*\n"
                f"   📖 {lesson['subject']}\n"
                f"   👤 {lesson['teacher']}\n"
                f"   🏫 {lesson['room']}\n"
            )
        text = "\n".join(lines)

    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Інший день", callback_data=f"group_{group}")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="back_main")],
    ])
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard)


# події

async def menu_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not EVENTS:
        text = "🎉 *Найближчі події*\n\nНаразі заплановані події відсутні."
    else:
        lines = ["🎉 *Найближчі події у коледжі:*\n"]
        for event in EVENTS:
            lines.append(
                f"📌 *{event['title']}*\n"
                f"   🗓 {event['date']}\n"
                f"   🕐 {event['time']}\n"
                f"   📍 {event['location']}\n"
                f"   ℹ️ {event['description']}\n"
            )
        text = "\n".join(lines)

    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Головне меню", callback_data="back_main")]
    ])
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard)


# faq

def faq_list_keyboard():
    buttons = [
        [InlineKeyboardButton(f"❓ {q['short']}", callback_data=f"faq_{i}")]
        for i, q in enumerate(FAQ)
    ]
    buttons.append([InlineKeyboardButton("◀️ Головне меню", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)


async def menu_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "❓ *Поширені питання*\n\nОберіть питання, що вас цікавить:",
        parse_mode="Markdown",
        reply_markup=faq_list_keyboard()
    )


async def show_faq_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    idx = int(query.data.replace("faq_", ""))
    item = FAQ[idx]

    text = f"❓ *{item['question']}*\n\n{item['answer']}"

    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ До питань", callback_data="menu_faq")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="back_main")],
    ])
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard)


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Я поки не вмію відповідати на довільні повідомлення \n"
        "Скористайтесь меню нижче:",
        reply_markup=main_menu_keyboard()
    )


# запуск

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu",  start))
    app.add_handler(CallbackQueryHandler(back_to_main,     pattern="^back_main$"))
    app.add_handler(CallbackQueryHandler(menu_schedule,    pattern="^menu_schedule$"))
    app.add_handler(CallbackQueryHandler(show_group_days,  pattern="^group_"))
    app.add_handler(CallbackQueryHandler(show_day_schedule, pattern="^day_"))
    app.add_handler(CallbackQueryHandler(menu_events,      pattern="^menu_events$"))
    app.add_handler(CallbackQueryHandler(menu_faq,         pattern="^menu_faq$"))
    app.add_handler(CallbackQueryHandler(show_faq_answer,  pattern="^faq_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))

    logger.info("Бот запущено...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
