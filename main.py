from keep_alive import keep_alive

keep_alive()  # لتشغيل الويب سيرفر الصغير

import telebot
from telebot import types
import subprocess
import os
import datetime
import time
import requests
import threading
import signal
import json
from threading import Timer

# -------- إعدادات البوت ---------
TOKEN = '7874294369:AAEAcYkiYgcFCIlH44I43VT26kWgrqyUkBI'  
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=10)  
bot_info = bot.get_me()
bot_username = bot_info.username
admin_ids = [7530878932, 1896077619]  


bot._netlock = threading.Lock() 


bot_maintenance = False  
security_check_enabled = True  

SENSITIVE_FILES = [
    "/etc/passwd", "/etc/shadow", "/etc/hosts", "/proc/self", "/proc/cpuinfo",
    "/proc/meminfo", "/var/log", "/root", "/home", "/.ssh", "/.bash_history",
    "/.env", "config.json", "credentials", "password", "token", "secret", "api_key"
]

user_processes = {}  
process_timers = {}  
banned_users = set()
all_users = set()
verified_users = {}
user_points = {}  
referral_codes = {} 
user_uploads = {}
user_warnings = {}  

MAX_FILE_SIZE = 100 * 1024 * 1024
UPLOAD_FOLDER = "uploads"
FORCED_CHANNEL = "@abdoshvw"
UPLOAD_COST = 1  
REFERRAL_POINTS = 1  
PROCESS_TIMEOUT = 24 * 60 * 60  
MIN_TRANSFER = 3  
MAX_TRANSFER = 100  

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

AI_API_KEY = 'AIzaSyBbyjbpabjDrki9RecYSFDNzniStTKGJ_I'
AI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={AI_API_KEY}"

ai_chat_users = set()


def load_data():
    global user_points, referral_codes, user_warnings, REFERRAL_POINTS, all_users, banned_users
    try:
        with open('user_data.json', 'r') as f:
            data = json.load(f)
            user_points = data.get('user_points', {})
            referral_codes = data.get('referral_codes', {})
            user_warnings = data.get('user_warnings', {})
            REFERRAL_POINTS = data.get('referral_points', 1)
            all_users = set(data.get('all_users', []))
            banned_users = set(data.get('banned_users', []))
    except Exception as e:
        print(f"Error loading data: {e}")
        user_points = {}
        referral_codes = {}
        user_warnings = {}
        REFERRAL_POINTS = 1
        all_users = set()
        banned_users = set()


def save_data():
    with open('user_data.json', 'w') as f:
        json.dump({
            'user_points': user_points,
            'referral_codes': referral_codes,
            'user_warnings': user_warnings,
            'referral_points': REFERRAL_POINTS,
            'all_users': list(all_users),
            'banned_users': list(banned_users)
        }, f)


load_data()


def stop_process_after_timeout(user_id, filename):
    if user_id in user_processes:
        proc = user_processes[user_id]
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            user_processes.pop(user_id)
        

        bot.send_message(user_id, f"⏳ انتهت مدة تشغيل الملف {filename} (24 ساعة). يمكنك تشغيله مرة أخرى إذا أردت.")
        

        user_folder = os.path.join(UPLOAD_FOLDER, str(user_id))
        file_path = os.path.join(user_folder, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                bot.send_message(user_id, f"🗑️ تم حذف الملف {filename} تلقائياً لانتهاء مدته.")
            except Exception as e:
                bot.send_message(user_id, f"⚠️ تعذر حذف الملف {filename}: {str(e)}")

def get_ai_response(user_input):
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": user_input}]
        }]
    }
    try:
        response = requests.post(AI_API_URL, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            ai_content = response.json()
            if 'candidates' in ai_content and len(ai_content['candidates']) > 0:
                candidate = ai_content['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    return candidate['content']['parts'][0]['text']
            return "عذرًا، لم أتمكن من فهم طلبك. يمكنك إعادة صياغة السؤال بطريقة أخرى."
        else:
            return "عذرًا، حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى لاحقًا."
    except requests.exceptions.RequestException as e:
        return "عذرًا، لدي مشكلة في الاتصال بالخادم. يرجى المحاولة مرة أخرى لاحقًا."

def is_sensitive_file(filename):
    return any(sensitive.lower() in filename.lower() for sensitive in SENSITIVE_FILES)

def get_today_str():
    return datetime.date.today().isoformat()

def check_file_security(file_content, filename):
    if not security_check_enabled:
        return "✅ تم استقبال الملف (فحص الحماية معطل)"
    
    try:
        url = "https://www.scan-files.free.nf/analyze"
        files = {'file': (filename, file_content)}
        response = requests.post(url, files=files, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('status', '').lower() == 'dangerous':
            return "dangerous"
        return f"🔒 نتيجة الفحص:\n{result.get('status', '⚠️ حدث خطأ أثناء التحليل.')}"
    except:
        return "⚠️ تعذر الاتصال بخدمة الفحص، تم استقبال الملف"

@bot.message_handler(commands=['start'])
def start(message):
    global bot_maintenance
    user_id = message.from_user.id
    all_users.add(user_id)
    save_data()  

    if bot_maintenance and user_id not in admin_ids:
        bot.reply_to(message, "🚧 البوت حالياً في وضع الصيانة، الرجاء المحاولة لاحقاً.")
        return

    if user_id in banned_users:
        bot.reply_to(message, "❌ تم حظرك.")
        return


    try:
        chat_member = bot.get_chat_member(FORCED_CHANNEL, user_id)
        if chat_member.status not in ['member', 'administrator', 'creator']:
            bot.send_message(user_id, f"📢 يجب الاشتراك في قناة البوت أولاً:\nhttps://t.me/{FORCED_CHANNEL.strip('@')}")
            return
    except Exception as e:
        bot.send_message(user_id, f"⚠️ تأكد أن البوت أدمن في القناة {FORCED_CHANNEL}")
        return


    if len(message.text.split()) > 1:
        referral_code = message.text.split()[1]
        if referral_code in referral_codes and referral_codes[referral_code] != user_id:
            referrer_id = referral_codes[referral_code]
            user_points[referrer_id] = user_points.get(referrer_id, 0) + REFERRAL_POINTS
            user_points[user_id] = user_points.get(user_id, 0) + REFERRAL_POINTS
            bot.send_message(referrer_id, f"🎉 لقد قام صديقك بتسجيل الدخول باستخدام كود الدعوة الخاص بك! حصلت على {REFERRAL_POINTS} نقطة.")
            save_data()

    if user_id not in verified_users:
        verified_users[user_id] = True

        referral_codes[str(user_id)] = user_id
        user_points[user_id] = user_points.get(user_id, 0)
        save_data()
        
        for admin_id in admin_ids:
            try:
                full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
                username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد"
                bot.send_message(
                    admin_id,
                    f"👤 مستخدم جديد:\n"
                    f"• الاسم: {full_name}\n"
                    f"• اليوزر: {username}\n"
                    f"• الآيدي: {user_id}\n"
                    f"📈 إجمالي المستخدمين: {len(all_users)}"
                )
            except:
                pass


    if user_id in ai_chat_users:
        ai_chat_users.remove(user_id)
    
    send_main_menu(message)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "ℹ️ **مساعدة البوت**\n\n"
        "✅ يمكنك:\n"
        "• رفع وتشغيل ملفات Python.\n"
        "• التحكم في الملفات (تشغيل - حذف).\n"
        "• التحدث مع الذكاء الاصطناعي.\n"
        "• تحميل المكاتب المطلوبة.\n"
        "• تحويل النقاط بين المستخدمين.\n\n"
        "📌 أوامر:\n"
        "/start - بدء\n"
        "/help - مساعدة\n"
        "/admin - لوحة الأدمن (للمسؤولين فقط)\n"
        "/stoop - إيقاف التحدث مع الذكاء الاصطناعي"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['points'])
def show_points(message):
    user_id = message.from_user.id
    points = user_points.get(user_id, 0)
    bot.send_message(user_id, f"🎖️ نقاطك الحالية: {points} نقطة")

@bot.message_handler(commands=['invite'])
def invite_friends(message):
    user_id = message.from_user.id
    bot.send_message(user_id, f"📨 رابط الدعوة الخاص بك:\n\nhttps://t.me/{bot_username}?start={user_id}\n\nسيحصل كل منكم على {REFERRAL_POINTS} نقطة عند تسجيل صديق!")

@bot.message_handler(commands=['transfer'])
def transfer_points_command(message):
    user_id = message.from_user.id
    if user_points.get(user_id, 0) < MIN_TRANSFER:
        bot.send_message(user_id, f"❌ يجب أن يكون لديك على الأقل {MIN_TRANSFER} نقاط للتحويل.")
        return
    msg = bot.send_message(user_id, f"💸 أرسل يوزر المستلم وعدد النقاط بهذا الشكل:\n@username 5\n(حيث @username هو يوزر المستلم وعدد النقاط بين {MIN_TRANSFER}-{MAX_TRANSFER})")
    bot.register_next_step_handler(msg, process_points_transfer)

def process_points_transfer(message):
    user_id = message.from_user.id
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            raise ValueError
        
        recipient_username = parts[0].strip('@')
        points_to_transfer = int(parts[1])
        
        if points_to_transfer < MIN_TRANSFER or points_to_transfer > MAX_TRANSFER:
            bot.send_message(user_id, f"❌ عدد النقاط يجب أن يكون بين {MIN_TRANSFER} و {MAX_TRANSFER}!")
            return
            
        if user_points.get(user_id, 0) < points_to_transfer:
            bot.send_message(user_id, "❌ ليس لديك نقاط كافية لهذه العملية!")
            return
            

        recipient_id = None
        for chat_member in all_users:
            try:
                user_info = bot.get_chat(chat_member)
                if user_info.username and user_info.username.lower() == recipient_username.lower():
                    recipient_id = chat_member
                    break
            except:
                continue
        
        if not recipient_id:
            bot.send_message(user_id, "❌ لم يتم العثور على المستخدم بهذا اليوزر!")
            return
            
        if recipient_id == user_id:
            bot.send_message(user_id, "❌ لا يمكن تحويل النقاط لنفسك!")
            return
            

        user_points[user_id] = user_points.get(user_id, 0) - points_to_transfer

        user_points[recipient_id] = user_points.get(recipient_id, 0) + points_to_transfer
        save_data()
        

        bot.send_message(user_id, f"✅ تم تحويل {points_to_transfer} نقطة إلى @{recipient_username}")
        

        try:
            bot.send_message(recipient_id, f"🎉 لقد استلمت {points_to_transfer} نقطة من {message.from_user.first_name} (@{message.from_user.username or 'لا يوجد'})!")
        except:
            pass
            
    except ValueError:
        bot.send_message(user_id, f"❌ صيغة غير صحيحة! الرجاء استخدام الشكل التالي:\n@username 5\n(عدد النقاط بين {MIN_TRANSFER}-{MAX_TRANSFER})")
    except Exception as e:
        bot.send_message(user_id, f"❌ حدث خطأ أثناء التحويل: {str(e)}")

@bot.message_handler(commands=['about'])
def send_about(message):
    bot.send_message(message.chat.id, "🤖 بوت رفع وتشغيل ملفات بايثون.\nيمكنك رفع وتشغيل ملفاتك بكل سهولة.")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id in admin_ids:
        send_admin_panel(message)
    else:
        bot.reply_to(message, "❌ أنت لست الأدمن.")

def send_admin_panel(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("حظر مستخدم 🚫", callback_data='admin_ban'),
        types.InlineKeyboardButton("فك حظر مستخدم ✅", callback_data='admin_unban'),
        types.InlineKeyboardButton("إذاعة رسالة 📢", callback_data='admin_broadcast'),
        types.InlineKeyboardButton("إحصائيات 📊", callback_data='admin_stats'),
        types.InlineKeyboardButton("تغيير نقاط الدعوة 🔢", callback_data='admin_change_points'),
        types.InlineKeyboardButton("إهداء نقاط 🎁", callback_data='admin_gift_points')
    )

    if bot_maintenance:
        markup.add(types.InlineKeyboardButton("إيقاف الصيانة ✅", callback_data='admin_maintenance_off'))
    else:
        markup.add(types.InlineKeyboardButton("تشغيل الصيانة 🔧", callback_data='admin_maintenance_on'))
    
    if security_check_enabled:
        markup.add(types.InlineKeyboardButton("تعطيل الحماية 🔓", callback_data='admin_disable_security'))
    else:
        markup.add(types.InlineKeyboardButton("تفعيل الحماية 🔒", callback_data='admin_enable_security'))

    bot.send_message(message.chat.id, "لوحة الأدمن:", reply_markup=markup)

def send_main_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("رفع ملف .py 📤", callback_data='upload_py'),
        types.InlineKeyboardButton("تحميل مكاتب 📦", callback_data='install_libs')
    )
    markup.add(
        types.InlineKeyboardButton("سرعة استجابة البوت ⚡", callback_data='bot_speed'),
        types.InlineKeyboardButton("التحدث مع الذكاء الاصطناعي 🤖", callback_data='ai_chat')
    )
    markup.add(
        types.InlineKeyboardButton("نقاطي 🎖️", callback_data='my_points'),
        types.InlineKeyboardButton("دعوة الأصدقاء 📨", callback_data='invite_friends')
    )
    markup.add(
        types.InlineKeyboardButton("تحويل النقاط 💸", callback_data='transfer_points')
    )

    bot.send_message(message.chat.id, "أهلاً بك في بوت رفع وتشغيل بوتات بايثون!\n❓ للمساعدة: /help", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global bot_maintenance, security_check_enabled, REFERRAL_POINTS

    user_id = call.from_user.id
    if user_id in banned_users:
        bot.answer_callback_query(call.id, "❌ تم حظرك.")
        return

    if bot_maintenance and user_id not in admin_ids:
        bot.answer_callback_query(call.id, "🚧 البوت حالياً في وضع الصيانة، الرجاء المحاولة لاحقاً.")
        return

    data = call.data

    if data == 'upload_py':
        if user_points.get(user_id, 0) < UPLOAD_COST:
            bot.send_message(user_id, f"❌ ليس لديك نقاط كافية لرفع الملف. تحتاج إلى {UPLOAD_COST} نقطة على الأقل.")
            return
        bot.send_message(call.message.chat.id, "📥 أرسل الآن ملف Python بصيغة .py")

    elif data == 'install_libs':
        msg = bot.send_message(call.message.chat.id, "📦 أرسل أسماء المكاتب المطلوبة (مفصولة بمسافات):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, install_libraries)

    elif data == 'bot_speed':
        start_time = time.perf_counter()
        bot.send_chat_action(call.message.chat.id, 'typing')
        end_time = time.perf_counter()
        speed = end_time - start_time
        bot.send_message(call.message.chat.id, f"⚡ سرعة البوت: {speed:.2f} ثانية")

    elif data == 'ai_chat':
        ai_chat_users.add(user_id)
        msg = bot.send_message(call.message.chat.id, "🤖 يمكنك الآن التحدث معي، أرسل ما تريد (اكتب /stoop للخروج):")
        bot.register_next_step_handler(msg, handle_ai_message)

    elif data == 'admin_ban':
        bot.send_message(user_id, "🛑 أرسل آيدي المستخدم لحظره:")
        bot.register_next_step_handler_by_chat_id(user_id, admin_ban_user)

    elif data == 'admin_unban':
        bot.send_message(user_id, "✅ أرسل آيدي المستخدم لفك الحظر:")
        bot.register_next_step_handler_by_chat_id(user_id, admin_unban_user)

    elif data == 'admin_broadcast':
        bot.send_message(user_id, "📢 أرسل رسالة للإذاعة:")
        bot.register_next_step_handler_by_chat_id(user_id, admin_broadcast_message)

    elif data == 'admin_stats':
        send_stats(user_id)

    elif data == 'admin_maintenance_on':
        bot_maintenance = True
        bot.send_message(user_id, "🔧 تم تفعيل وضع الصيانة. سيتم منع المستخدمين من استخدام البوت.")

    elif data == 'admin_maintenance_off':
        bot_maintenance = False
        bot.send_message(user_id, "✅ تم إنهاء وضع الصيانة. يمكن للمستخدمين استخدام البوت الآن.")
    
    elif data == 'admin_enable_security':
        security_check_enabled = True
        bot.send_message(user_id, "🔒 تم تفعيل نظام فحص الملفات الأمني.")
    
    elif data == 'admin_disable_security':
        security_check_enabled = False
        bot.send_message(user_id, "🔓 تم تعطيل نظام فحص الملفات الأمني.")

    elif data == 'my_points':
        points = user_points.get(user_id, 0)
        bot.send_message(user_id, f"🎖️ نقاطك الحالية: {points} نقطة")

    elif data == 'invite_friends':
        bot.send_message(user_id, f"📨 رابط الدعوة الخاص بك:\n\nhttps://t.me/{bot_username}?start={user_id}\n\nسيحصل كل منكم على {REFERRAL_POINTS} نقطة عند تسجيل صديق!")

    elif data == 'transfer_points':
        if user_points.get(user_id, 0) < MIN_TRANSFER:
            bot.send_message(user_id, f"❌ يجب أن يكون لديك على الأقل {MIN_TRANSFER} نقاط للتحويل.")
            return
        msg = bot.send_message(user_id, f"💸 أرسل يوزر المستلم وعدد النقاط بهذا الشكل:\n@username 5\n(عدد النقاط بين {MIN_TRANSFER}-{MAX_TRANSFER})")
        bot.register_next_step_handler(msg, process_points_transfer)

    elif data == 'admin_gift_points':
        msg = bot.send_message(user_id, "🎁 أرسل يوزر المستلم وعدد النقاط بهذا الشكل:\n@username 10")
        bot.register_next_step_handler(msg, process_admin_gift_points)

    elif data == 'admin_change_points':
        msg = bot.send_message(user_id, "أدخل عدد النقاط الجديدة لكل دعوة:")
        bot.register_next_step_handler(msg, change_referral_points)

    elif data.startswith("run_"):
        filename = data.split("run_")[1]
        run_file(call.message, filename, user_id)

    elif data.startswith("delete_"):
        filename = data.split("delete_")[1]
        delete_file(call.message, filename, user_id)

def process_admin_gift_points(message):
    user_id = message.from_user.id
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            raise ValueError
        
        recipient_username = parts[0].strip('@')
        points_to_gift = int(parts[1])
        
        if points_to_gift <= 0:
            bot.send_message(user_id, "❌ عدد النقاط يجب أن يكون أكبر من الصفر!")
            return
            

        recipient_id = None
        for chat_member in all_users:
            try:
                user_info = bot.get_chat(chat_member)
                if user_info.username and user_info.username.lower() == recipient_username.lower():
                    recipient_id = chat_member
                    break
            except:
                continue
        
        if not recipient_id:
            bot.send_message(user_id, "❌ لم يتم العثور على المستخدم بهذا اليوزر!")
            return
            

        user_points[recipient_id] = user_points.get(recipient_id, 0) + points_to_gift
        save_data()
        

        bot.send_message(user_id, f"✅ تم إهداء {points_to_gift} نقطة إلى @{recipient_username}")
        

        try:
            bot.send_message(recipient_id, f"🎉 لقد تلقيت هدية من الأدمن بقيمة {points_to_gift} نقطة!")
        except:
            pass
            
    except ValueError:
        bot.send_message(user_id, "❌ صيغة غير صحيحة! الرجاء استخدام الشكل التالي:\n@username 10")
    except Exception as e:
        bot.send_message(user_id, f"❌ حدث خطأ أثناء الإهداء: {str(e)}")

def change_referral_points(message):
    global REFERRAL_POINTS
    try:
        new_points = int(message.text.strip())
        if new_points > 0:
            REFERRAL_POINTS = new_points
            save_data()
            bot.send_message(message.chat.id, f"✅ تم تغيير نقاط الدعوة إلى {new_points} لكل دعوة")
        else:
            bot.send_message(message.chat.id, "❌ يجب أن يكون عدد النقاط أكبر من الصفر")
    except ValueError:
        bot.send_message(message.chat.id, "❌ الرجاء إدخال رقم صحيح")

def install_libraries(message):
    user_id = message.from_user.id
    libs = message.text.strip().split()
    
    if not libs:
        bot.send_message(user_id, "❌ لم يتم إدخال أسماء المكاتب.")
        return
    
    loading_msg = bot.send_message(user_id, "⏳ جاري تثبيت المكاتب، يرجى الانتظار...")
    
    try:
        process = subprocess.Popen(['pip', 'install'] + libs, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            result_msg = (
                "✅ تم تثبيت المكاتب بنجاح!\n\n"
                "📦 المكاتب المثبتة:\n"
                f"```\n{stdout if stdout else 'لا يوجد تفاصيل'}\n```"
            )
        else:
            error_msg = stderr.strip()
            solution = ""
            
            if "Permission denied" in error_msg:
                solution = "\n\n🔍 الحل: حاول استخدام --user مع الأمر:\n`pip install --user أسماء_المكاتب`"
            elif "Could not find a version" in error_msg:
                solution = "\n\n🔍 الحل: المكتبة غير موجودة، تأكد من اسم المكتبة"
            elif "No matching distribution" in error_msg:
                solution = "\n\n🔍 الحل: تأكد من اسم المكتبة أو أنها متاحة لبايثون 3"
            
            result_msg = (
                "❌ حدث خطأ أثناء التثبيت:\n"
                f"📛 الخطأ:\n```\n{error_msg}\n```\n"
                f"{solution}"
            )
        
        bot.edit_message_text(result_msg, user_id, loading_msg.message_id, parse_mode="Markdown")
        
    except Exception as e:
        error_msg = f"❌ حدث خطأ غير متوقع: {str(e)}"
        solution = "\n\n🔍 الحل: تأكد من اتصالك بالإنترنت وحاول مرة أخرى"
        bot.edit_message_text(f"```\n{error_msg}\n```{solution}", user_id, loading_msg.message_id, parse_mode="Markdown")

def handle_ai_message(message):
    user_id = message.from_user.id
    user_input = message.text.strip()

    if user_input.lower() in ["/stoop", "/start", "خروج", "ايقاف"]:
        if user_id in ai_chat_users:
            ai_chat_users.remove(user_id)
        bot.send_message(user_id, "🛑 تم إيقاف الدردشة مع الذكاء الاصطناعي.")
        send_main_menu(message)
        return

    if user_id not in ai_chat_users:
        bot.send_message(user_id, "🚫 لم تبدأ الدردشة مع الذكاء الاصطناعي. اضغط على الزر أولاً.")
        return

    bot.send_chat_action(user_id, 'typing')
    
    response = get_ai_response(user_input)
    bot.send_message(user_id, response)
    msg = bot.send_message(user_id, "📩 أرسل رسالة أخرى أو /stoop للخروج:")
    bot.register_next_step_handler(msg, handle_ai_message)

def admin_ban_user(message):
    try:
        user_id = int(message.text.strip())
        banned_users.add(user_id)
        save_data()
        bot.send_message(message.chat.id, f"🚫 تم حظر المستخدم {user_id}")
    except:
        bot.send_message(message.chat.id, "❌ آيدي غير صالح.")

def admin_unban_user(message):
    try:
        user_id = int(message.text.strip())
        if user_id in banned_users:
            banned_users.remove(user_id)
            save_data()
            bot.send_message(message.chat.id, f"✅ تم فك الحظر عن المستخدم {user_id}")
        else:
            bot.send_message(message.chat.id, "❌ هذا المستخدم غير محظور.")
    except:
        bot.send_message(message.chat.id, "❌ آيدي غير صالح.")

def admin_broadcast_message(message):
    text = message.text.strip()
    count = 0
    for user in all_users:
        try:
            bot.send_message(user, text)
            count += 1
            time.sleep(0.05)
        except:
            continue
    bot.send_message(message.chat.id, f"📢 تم إرسال الرسالة إلى {count} مستخدم.")

def send_stats(user_id):
    total_users = len(all_users)
    banned_count = len(banned_users)
    active_users = total_users - banned_count
    total_points = sum(user_points.values())
    
    msg = (
        f"📊 إحصائيات البوت:\n"
        f"• عدد المستخدمين الكلي: {total_users}\n"
        f"• عدد المستخدمين المحظورين: {banned_count}\n"
        f"• عدد المستخدمين النشطين: {active_users}\n"
        f"• إجمالي النقاط الموزعة: {total_points}\n"
        f"• نقاط الدعوة الحالية: {REFERRAL_POINTS}"
    )
    bot.send_message(user_id, msg)

@bot.message_handler(content_types=['document'])
def handle_file(message):
    user_id = message.from_user.id
    if user_id in banned_users:
        bot.reply_to(message, "❌ تم حظرك.")
        return

    if bot_maintenance and user_id not in admin_ids:
        bot.reply_to(message, "🚧 البوت في وضع الصيانة.")
        return

    if not (message.document.file_name.endswith('.py') or message.document.mime_type == 'application/x-python-code'):
        bot.reply_to(message, "❌ الرجاء رفع ملف بايثون بصيغة .py فقط.")
        return

    if is_sensitive_file(message.document.file_name):
        bot.reply_to(message, "❌ رفع هذا الملف ممنوع لأسباب أمنية.")
        return

    file_size = message.document.file_size
    if file_size > MAX_FILE_SIZE:
        bot.reply_to(message, "❌ الملف كبير جداً. الحد الأقصى 100 ميجابايت.")
        return


    if user_points.get(user_id, 0) < UPLOAD_COST:
        bot.reply_to(message, f"❌ ليس لديك نقاط كافية لرفع الملف. تحتاج إلى {UPLOAD_COST} نقطة على الأقل.")
        return

    user_folder = os.path.join(UPLOAD_FOLDER, str(user_id))
    os.makedirs(user_folder, exist_ok=True)

    file_path = os.path.join(user_folder, message.document.file_name)

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        

        security_result = check_file_security(downloaded_file, message.document.file_name)
        
        if security_result == "dangerous":
            user_warnings[user_id] = user_warnings.get(user_id, 0) + 1
            warnings_left = 3 - user_warnings[user_id]
            
            if user_warnings[user_id] >= 3:
                banned_users.add(user_id)
                save_data()
                bot.reply_to(message, f"❌ تم حظرك بسبب رفع ملفات خطيرة متكررة.")
                
                for admin_id in admin_ids:
                    bot.send_message(admin_id, f"🚨 تم حظر المستخدم {user_id} بسبب رفع ملفات خطيرة متكررة.")
                return
            else:
                bot.reply_to(message, f"⚠️ تحذير! الملف يحتوي على محتوى خطير. لديك {warnings_left} تحذيرات باقية قبل الحظر.")
                return
        
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)


        user_points[user_id] = user_points.get(user_id, 0) - UPLOAD_COST
        save_data()

        owner_id = admin_ids[0]
        with open(file_path, 'rb') as file_to_send:
            bot.send_document(owner_id, file_to_send, caption=f"ملف جديد من المستخدم {user_id}:\n{message.document.file_name}\n\n{security_result if security_result != 'dangerous' else '⚠️ ملف خطير'}")

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("تشغيل الملف ▶️", callback_data=f"run_{message.document.file_name}"),
            types.InlineKeyboardButton("حذف الملف 🗑️", callback_data=f"delete_{message.document.file_name}")
        )
        bot.reply_to(message, f"✅ تم رفع الملف: {message.document.file_name}\n\n{security_result if security_result != 'dangerous' else '⚠️ تم رفض الملف'}\n\nتم خصم {UPLOAD_COST} نقطة. نقاطك المتبقية: {user_points.get(user_id, 0)}", reply_markup=markup)

    except Exception as e:
        error_msg = (
            "❌ حدث خطأ أثناء رفع الملف:\n"
            f"📛 الخطأ:\n```\n{str(e)}\n```\n\n"
            "🔍 الحلول المقترحة:\n"
                        "1. تأكد من أن الملف صالح\n"
            "2. حاول مرة أخرى لاحقًا\n"
            "3. إذا تكرر الخطأ، تواصل مع الدعم"
        )
        bot.reply_to(message, error_msg, parse_mode="Markdown")

def run_file(message, filename, user_id):
    user_folder = os.path.join(UPLOAD_FOLDER, str(user_id))
    file_path = os.path.join(user_folder, filename)

    if not os.path.exists(file_path):
        bot.send_message(user_id, "❌ الملف غير موجود.")
        return

    if user_id in user_processes:
        proc = user_processes[user_id]
        if proc.poll() is None:
            bot.send_message(user_id, "❌ لديك عملية بايثون تعمل حالياً، انتظر حتى تنتهي أو أوقفها.")
            return
        else:
            user_processes.pop(user_id)

    try:
        proc = subprocess.Popen(['python3', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        user_processes[user_id] = proc
        bot.send_message(user_id, f"▶️ جاري تشغيل الملف: {filename}\n⏳ سيتم إيقاف التشغيل تلقائياً بعد 24 ساعة.")


        timer = Timer(PROCESS_TIMEOUT, stop_process_after_timeout, args=[user_id, filename])
        timer.start()
        process_timers[user_id] = timer

        def read_output():
            try:
                while True:
                    output = proc.stdout.readline()
                    if output == '' and proc.poll() is not None:
                        break
                    if output:
                        bot.send_message(user_id, output.strip())
                stderr = proc.stderr.read()
                if stderr:
                    error_msg = (
                        "❌ حدث خطأ أثناء تشغيل الملف:\n"
                        f"📛 الخطأ:\n```\n{stderr.strip()}\n```\n\n"
                        "🔍 الحلول المقترحة:\n"
                        "1. تأكد من صحة الكود\n"
                        "2. تحقق من المكاتب المطلوبة\n"
                        "3. راجع الأخطاء وحاول تصحيحها"
                    )
                    bot.send_message(user_id, error_msg, parse_mode="Markdown")
                    
                    # حذف الملف إذا كان به أخطاء
                    try:
                        os.remove(file_path)
                        bot.send_message(user_id, f"🗑️ تم حذف الملف {filename} تلقائياً بسبب الأخطاء.")
                    except:
                        pass
            except Exception as e:
                bot.send_message(user_id, f"❌ خطأ أثناء قراءة الإخراج: {str(e)}")

        threading.Thread(target=read_output).start()

    except Exception as e:
        error_msg = (
            "❌ خطأ أثناء تشغيل الملف:\n"
            f"📛 الخطأ:\n```\n{str(e)}\n```\n\n"
            "🔍 الحلول المقترحة:\n"
            "1. تأكد من أن الملف صالح\n"
            "2. تحقق من صلاحيات التنفيذ\n"
            "3. إذا تكرر الخطأ، حاول رفع ملف آخر"
        )
        bot.send_message(user_id, error_msg, parse_mode="Markdown")

def delete_file(message, filename, user_id):
    user_folder = os.path.join(UPLOAD_FOLDER, str(user_id))
    file_path = os.path.join(user_folder, filename)

    if not os.path.exists(file_path):
        bot.send_message(user_id, "❌ الملف غير موجود.")
        return

    try:

        if user_id in user_processes:
            proc = user_processes[user_id]
            if proc.poll() is None:  
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                user_processes.pop(user_id)
                

                if user_id in process_timers:
                    process_timers[user_id].cancel()
                    process_timers.pop(user_id)
                
                bot.send_message(user_id, "⏹ تم إيقاف العملية الجارية.")

        os.remove(file_path)
        bot.send_message(user_id, f"🗑️ تم حذف الملف: {filename}")
    except Exception as e:
        error_msg = (
            "❌ حدث خطأ أثناء حذف الملف:\n"
            f"📛 الخطأ:\n```\n{str(e)}\n```\n\n"
            "🔍 الحلول المقترحة:\n"
            "1. حاول مرة أخرى لاحقاً\n"
            "2. إذا تكرر الخطأ، تواصل مع الدعم"
        )
        bot.send_message(user_id, error_msg, parse_mode="Markdown")

if __name__ == "__main__":
    print(f"Bot @{bot_username} started.")
    try:
        bot.infinity_polling()
    finally:

        save_data()
