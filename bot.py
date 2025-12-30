import os
import json
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# بارگیری توکن از فایل .env
load_dotenv()
TOKEN = os.getenv("TOKEN")

# بارگیری سوالات از فایل JSON
with open('quiz_data.json', 'r', encoding='utf-8') as f:
    QUIZ_DATA = json.load(f)

# دیکشنری برای ذخیره امتیازات کاربران
user_scores = {}

# دستور start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""
    سلام {user.first_name}!
    به **Quiz Arena ⚽** خوش آمدید!

    🎯 اینجا می‌تونی دانش فوتبالی خودت رو محک بزنی!
    
    دستورات:
    /start - شروع مجدد
    /quiz - شروع کوییز جدید
    /score - امتیاز تو
    /help - راهنمایی
    
    آماده‌ای؟ دکمه زیر رو بزن!
    """
    
    keyboard = [
        [InlineKeyboardButton("🎯 شروع کوییز ⚽", callback_data='start_quiz')],
        [InlineKeyboardButton("🏆 جدول امتیازات", callback_data='leaderboard')],
        [InlineKeyboardButton("📊 امتیاز من", callback_data='my_score')],
        [InlineKeyboardButton("ℹ️ راهنمایی", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

# شروع کوییز
async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    context.user_data['current_question'] = 0
    context.user_data['score'] = 0
    context.user_data['user_id'] = user_id
    
    await send_question(update, context)

# ارسال سوال
async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    question_index = context.user_data['current_question']
    
    if question_index >= len(QUIZ_DATA):
        await show_results(update, context)
        return
    
    question = QUIZ_DATA[question_index]
    
    # ایجاد دکمه‌های گزینه‌ها
    buttons = []
    for i, option in enumerate(question['options']):
        buttons.append([InlineKeyboardButton(f"{chr(65+i)}. {option}", callback_data=f'answer_{i}')])
    
    # دکمه لغو
    buttons.append([InlineKeyboardButton("❌ لغو کوییز", callback_data='cancel_quiz')])
    
    markup = InlineKeyboardMarkup(buttons)
    
    text = f"""
    📝 سوال {question_index + 1} از {len(QUIZ_DATA)}
    
    ⚽ **{question['question']}**
    
    زمان پاسخ: ۳۰ ثانیه ⏰
    """
    
    await query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

# پردازش پاسخ
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    answer_index = int(query.data.split('_')[1])
    question_index = context.user_data['current_question']
    question = QUIZ_DATA[question_index]
    
    # بررسی پاسخ
    if answer_index == question['correct']:
        context.user_data['score'] += 10
        result_text = "✅ **درست جواب دادی!** +۱۰ امتیاز 🎉"
    else:
        correct_answer = question['options'][question['correct']]
        result_text = f"❌ **اشتباه!** پاسخ صحیح: {correct_answer}"
    
    await query.edit_message_text(text=result_text, parse_mode='Markdown')
    
    # رفتن به سوال بعدی
    context.user_data['current_question'] += 1
    await asyncio.sleep(2)
    await send_question(update, context)

# نمایش نتایج
async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = context.user_data['user_id']
    score = context.user_data['score']
    total = len(QUIZ_DATA) * 10
    
    # ذخیره امتیاز
    if user_id not in user_scores:
        user_scores[user_id] = []
    user_scores[user_id].append({
        'score': score,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'total_questions': len(QUIZ_DATA)
    })
    
    # تعیین رتبه
    if score == total:
        rank = "🏆 قهرمان مطلق!"
    elif score >= total * 0.7:
        rank = "🎖️ حرفه‌ای فوتبال"
    elif score >= total * 0.5:
        rank = "⭐ بازیکن متوسط"
    else:
        rank = "🌱 تازه‌کار"
    
    result_text = f"""
    🎊 **کوییز به پایان رسید!**
    
    📊 نتایج شما:
    امتیاز: **{score}/{total}**
    رتبه: {rank}
    
    ✅ پاسخ‌های صحیح: {score // 10}
    ❌ پاسخ‌های اشتباه: {len(QUIZ_DATA) - (score // 10)}
    
    دوباره بازی کنی؟
    """
    
    keyboard = [
        [InlineKeyboardButton("🔄 بازی مجدد", callback_data='start_quiz')],
        [InlineKeyboardButton("🏆 جدول امتیازات", callback_data='leaderboard')],
        [InlineKeyboardButton("📋 منوی اصلی", callback_data='main_menu')]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=result_text, reply_markup=markup, parse_mode='Markdown')

# جدول امتیازات
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not user_scores:
        text = "هنوز کسی بازی نکرده! اولین نفر باش! 🏆"
    else:
        # محاسبه بهترین امتیاز هر کاربر
        best_scores = {}
        for user_id, scores in user_scores.items():
            best_scores[user_id] = max([s['score'] for s in scores])
        
        # مرتب‌سازی
        sorted_scores = sorted(best_scores.items(), key=lambda x: x[1], reverse=True)[:10]
        
        text = "🏆 **جدول برترین‌ها:**\n\n"
        for i, (user_id, score) in enumerate(sorted_scores):
            try:
                user = await context.bot.get_chat(user_id)
                name = user.first_name or "کاربر"
            except:
                name = "کاربر"
            
            medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][i] if i < 10 else f"{i+1}."
            text += f"{medal} {name}: **{score}** امتیاز\n"
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='main_menu')]]
    markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

# امتیاز کاربر
async def show_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id in user_scores:
        scores = user_scores[user_id]
        total_games = len(scores)
        best_score = max([s['score'] for s in scores])
        avg_score = sum([s['score'] for s in scores]) // total_games
        
        text = f"""
        📊 **آمار شما:**
        
        🎮 تعداد بازی‌ها: **{total_games}**
        🏆 بهترین امتیاز: **{best_score}**
        📈 میانگین امتیاز: **{avg_score}**
        📅 آخرین بازی: {scores[-1]['date']}
        
        ادامه بده! 💪
        """
    else:
        text = "هنوز بازی نکردی! اولین کوییز رو شروع کن! ⚽"
    
    keyboard = [
        [InlineKeyboardButton("🎯 شروع کوییز", callback_data='start_quiz')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='main_menu')]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

# راهنمایی
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """
    📖 **راهنمای Quiz Arena:**
    
    🎮 **نحوه بازی:**
    ۱. روی «شروع کوییز» کلیک کن
    ۲. به سوالات فوتبالی پاسخ بده
    ۳. برای هر پاسخ صحیح ۱۰ امتیاز بگیر
    ۴. در جدول امتیازات رقابت کن
    
    🏆 **سیستم امتیازدهی:**
    ✅ پاسخ صحیح: +۱۰ امتیاز
    ❌ پاسخ اشتباه: ۰ امتیاز
    ⏰ زمان هر سوال: ۳۰ ثانیه
    
    📊 **دستورات:**
    /start - شروع ربات
    /quiz - شروع کوییز جدید
    /score - نمایش امتیاز تو
    /help - این راهنما
    
    🔧 **پشتیبانی:**
    برای گزارش مشکل با @QzArenaBot_admin ارتباط برقرار کن
    """
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='main_menu')]]
    markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

# منوی اصلی
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

# لغو کوییز
async def cancel_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = "کوییز لغو شد! 😊\nمی‌خوای دوباره شروع کنی؟"
    
    keyboard = [
        [InlineKeyboardButton("🔄 بله، شروع کن", callback_data='start_quiz')],
        [InlineKeyboardButton("📋 منوی اصلی", callback_data='main_menu')]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=markup)

# خطا
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"خطا: {context.error}")
    if update.callback_query:
        await update.callback_query.message.reply_text("⚠️ خطایی رخ داد! لطفا دوباره تلاش کن.")

# تابع اصلی
def main():
    if not TOKEN:
        print("❌ توکن یافت نشد! فایل .env را بررسی کنید.")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    # دستورات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("quiz", start_quiz))
    app.add_handler(CommandHandler("score", show_score))
    
    # Callback Query Handlers
    app.add_handler(CallbackQueryHandler(start_quiz, pattern='^start_quiz$'))
    app.add_handler(CallbackQueryHandler(handle_answer, pattern='^answer_'))
    app.add_handler(CallbackQueryHandler(leaderboard, pattern='^leaderboard$'))
    app.add_handler(CallbackQueryHandler(show_score, pattern='^my_score$'))
    app.add_handler(CallbackQueryHandler(help_command, pattern='^help$'))
    app.add_handler(CallbackQueryHandler(main_menu, pattern='^main_menu$'))
    app.add_handler(CallbackQueryHandler(cancel_quiz, pattern='^cancel_quiz$'))
    
    # خطا
    app.add_error_handler(error_handler)
    
    print("✅ ربات در حال اجراست...")
    print(f"🔗 آدرس ربات: https://t.me/QzArenaBot")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    import asyncio
    main()
