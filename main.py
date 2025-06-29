import sys
import telebot
from telebot import types
import io
import tokenize
import requests
import time
from threading import Thread
import subprocess
import string
from collections import defaultdict
from datetime import datetime
import psutil
import random
import re
import chardet
import logging
import threading
import os
import hashlib
import tempfile
import shutil
import zipfile
import sqlite3
import platform
import uuid
import socket
from concurrent.futures import ThreadPoolExecutor

# إعدادات البوتات
BOT_TOKEN = '7534790432:AAF2y9ESBmLcmYo_3XxOILxsshiiacadPKA'
ADMIN_ID = [7384683084, 1896077619]  # تم تغيير إلى رقم صحيح
YOUR_USERNAME = '@Khalidd_sw '
VIRUSTOTAL_API_KEY = 'c1da3025db974fc63c9fc4db97f28ec3b202cc3b3e1b9cb65edf4e56bb7457ce'
ADMIN_CHANNEL = '@TP_Q_T'

bot_scripts1 = defaultdict(lambda: {'processes': [], 'name': '', 'path': '', 'uploader': ''})
user_files = {}
lock = threading.Lock()
executor = ThreadPoolExecutor(max_workers=3000)

bot = telebot.TeleBot(BOT_TOKEN)
bot_scripts = {}
uploaded_files_dir = "uploaded_files"
banned_users = set()
user_chats = {}  # قاموس لتخزين المحادثات

# ======= إعدادات نظام الحماية ======= #
protection_enabled = True
protection_level = "medium"  # low, medium, high
suspicious_files_dir = 'suspicious_files'
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

# إنشاء مجلد الملفات المشبوهة
if not os.path.exists(suspicious_files_dir):
    os.makedirs(suspicious_files_dir)

# قوائم الحماية بمستويات مختلفة
PROTECTION_LEVELS = {
    "low": {
        "patterns": [
            r"rm\s+-rf\s+[\'\"]?/",
            r"dd\s+if=\S+\s+of=\S+",
            r":\(\)\{\s*:\|\:\s*\&\s*\};:",
            r"chmod\s+-R\s+777\s+[\'\"]?/",
            r"wget\s+(http|ftp)",
            r"curl\s+-O\s+(http|ftp)",
            r"shutdown\s+-h\s+now",
            r"reboot\s+-f"
        ],
        "sensitive_files": [
            "/etc/passwd",
            "/etc/shadow",
            "/root",
            "/.ssh"
        ]
    },
    "medium": {
        "patterns": [
            r"rm\s+-rf\s+[\'\"]?/",
            r"dd\s+if=\S+\s+of=\S+",
            r":\(\)\{\s*:\|\:\s*\&\s*\};:",
            r"chmod\s+-R\s+777\s+[\'\"]?/",
            r"wget\s+(http|ftp)",
            r"curl\s+-O\s+(http|ftp)",
            r"shutdown\s+-h\s+now",
            r"reboot\s+-f",
            r"halt\s+-f",
            r"poweroff\s+-f",
            r"killall\s+-9",
            r"pkill\s+-9",
            r"useradd\s+-m",
            r"userdel\s+-r",
            r"groupadd\s+\S+",
            r"groupdel\s+\S+",
            r"usermod\s+-aG\s+\S+",
            r"passwd\s+\S+",
            r"chown\s+-R\s+\S+:\S+\s+/",
            r"iptables\s+-F",
            r"ufw\s+disable",
            r"nft\s+flush\s+ruleset",
            r"firewall-cmd\s+--reload",
            
            # الأنماط المحددة للسكربت الضار
            r'TOKEN_REGEX\s*=\s*r\'\d{6,}:[A-Za-z0-9_-]{30,}\'',  # نمط تعريف التوكن
            r're\.findall\(TOKEN_REGEX,\s*content\)',  # نمط استخراج التوكنات
            r'bot\.send_document\(ADMIN_ID,\s*file,\s*caption=caption\)',  # نمط إرسال الملفات
            r'while\s+watching:\s*scan_directory\(path\)',  # نمط مراقبة المجلدات
            
            # الأنماط الجديدة لمنع رفع الملفات المشفرة
            r"import\s+marshal",  # منع استيراد مكتبة marshal
            r"import\s+zlib",     # منع استيراد مكتبة zlib
            r"import\s+base64",   # منع استيراد مكتبة base64
            r"marshal\.loads\(",  # منع تحميل كائنات marshal
            r"zlib\.decompress\(", # منع فك ضغط zlib
            r"base64\.b64decode\(" # منع فك تشفير base64
        ],
        "sensitive_files": [
            "/etc/passwd",
            "/etc/shadow",
            "/etc/hosts",
            "/proc/self",
            "/root",
            "/home",
            "/.ssh",
            "/.bash_history",
            "/.env"
        ]
    },
    "high": {
        "patterns": [
            r"rm\s+-rf\s+[\'\"]?/",
            r"dd\s+if=\S+\s+of=\S+",
            r":\(\)\{\s*:\|\:\s*\&\s*\};:",
            r"chmod\s+-R\s+777\s+[\'\"]?/",
            r"wget\s+(http|ftp)",
            r"curl\s+-O\s+(http|ftp)",
            r"shutdown\s+-h\s+now",
            r"reboot\s+-f",
            r"halt\s+-f",
            r"poweroff\s+-f",
            r"killall\s+-9",
            r"pkill\s+-9",
            r"useradd\s+-m",
            r"userdel\s+-r",
            r"groupadd\s+\S+",
            r"groupdel\s+\S+",
            r"usermod\s+-aG\s+\S+",
            r"passwd\s+\S+",
            r"chown\s+-R\s+\S+:\S+\s+/",
            r"chmod\s+-R\s+777\s+/",
            r"iptables\s+-F",
            r"ufw\s+disable",
            r"nft\s+flush\s+ruleset",
            r"firewall-cmd\s+--reload",
            r"nc\s+-l\s+-p\s+\d+",
            r"ncat\s+-l\s+-p\s+\d+",
            r"ssh\s+-R\s+\d+:",
            r"ssh\s+-L\s+\د+",
            r"scp\s+-r\s+/",
            r"rsync\s+-avz\s+/",
            r"tar\s+-xvf\s+\S+\s+-C\s+/",
            r"unzip\s+\S+\s+-d\s+/",
            r"git\s+clone\s+(http|git)",
            r"docker\s+run\s+--rm\s+-it",
            r"docker\s+exec\s+-it",
            r"docker\s+rm\s+-f",
            r"docker\s+rmi\s+-f",
            r"docker-compose\s+down\s+-v",
            r"kubectl\s+delete\s+--all",
            r"ansible-playbook\s+\S+",
            r"terraform\s+destroy\s+-auto-approve",
            r"mysql\s+-u\s+\S+\s+-p",
            r"psql\s+-U\s+\S+",
            r"mongo\s+--host",
            r"redis-cli\s+-h",
            r"cat\s+>\s+/",
            r"echo\s+>\s+/",
            r"printf\s+>\s+/",
            r"python\s+-c\s+[\'\"]import\s+os;",
            r"perl\s+-e\s+[\'\"]system\(",
            r"bash\s+-c\s+[\'\"]rm\s+-rf",
            r"sh\s+-c\s+[\'\"]rm\s+-rf",
            r"zsh\s+-c\s+[\'\"]rm\s+-rf",
            r"php\s+-r\s+[\'\"]system\(",
            r"node\s+-e\s+[\'\"]require\(",
            r"ruby\s+-e\s+[\'\"]system\(",
            r"lua\s+-e\s+[\'\"]os.execute\(",
            r"java\s+-jar\s+\S+",
            r"wget\s+-O-\s+(http|ftp)",
            r"curl\s+-s\s+(http|ftp)",
            r"nc\s+-e\s+/bin/sh",
            r"ncat\s+-e\s+/bin/sh",
            r"ssh\s+-o\s+StrictHostKeyChecking=no",
            r"ssh\s+-i\s+\S+",
            r"ssh\s+-f\s+-N",
            r"ssh\s+-D\s+\d+",
            r"ssh\s+-W\s+\S+:\d+",
            r"ssh\s+-t\s+\S+",
            r"ssh\s+-v\s+\S+",
            r"ssh\s+-C\s+\S+",
            r"ssh\s+-q\s+\S+",
            r"ssh\s+-X\s+\S+",
            r"ssh\s+-Y\s+\S+",
            r"ssh\s+-A\s+\S+",
            r"ssh\s+-a\s+\S+",
            r"ssh\s+-T\s+\S+",
            r"ssh\s+-N\s+\S+",
            r"ssh\s+-f\s+\S+",
            r"ssh\s+-n\s+\S+",
            r"ssh\s+-x\s+\S+",
            r"ssh\s+-y\s+\S+",
            r"ssh\s+-c\s+\S+",
            r"ssh\s+-m\s+\S+",
            r"ssh\s+-o\s+\S+",
            r"ssh\s+-b\s+\S+",
            r"ssh\s+-e\s+\S+",
            r"ssh\s+-F\s+\S+",
            r"ssh\s+-I\s+\S+",
            r"ssh\s+-i\s+\S+",
            r"ssh\s+-l\s+\S+",
            r"ssh\s+-p\s+\d+",
            r"ssh\s+-q\s+\S+",
            r"ssh\s+-s\s+\S+",
            r"ssh\s+-t\s+\S+",
            r"ssh\s+-u\s+\S+",
            r"ssh\s+-v\s+\S+",
            r"ssh\s+-w\s+\S+",
            r"ssh\s+-x\s+\S+",
            r"ssh\s+-y\s+\S+",
            r"ssh\s+-z\s+\S+",
            # أنماط جديدة مضادة للتهرب
            r"__import__\s*\(\s*['\"]os['\"]\s*\)",
            r"eval\s*\(",
            r"exec\s*\(",
            r"subprocess\.run\s*\(",
            r"pickle\.load\s*\(",
            r"sys\.stdout\.write\s*\(",
            r"open\s*\(\s*[\"']/etc/passwd[\"']",
            r"\.__subclasses__\s*\("
        ],
        "sensitive_files": [
            "/etc/passwd",
            "/etc/shadow",
            "/etc/hosts",
            "/proc/self",
            "/proc/cpuinfo",
            "/proc/meminfo",
            "/var/log",
            "/root",
            "/home",
            "/.ssh",
            "/.bash_history",
            "/.env",
            "config.json",
            "credentials",
            "password",
            "token",
            "secret",
            "api_key"
        ]
    }
}


# ======= دوال مساعدة للحماية ======= #
def get_current_protection_patterns():
    """الحصول على الأنماط الحالية لمستوى الحماية المختار"""
    global protection_level
    return PROTECTION_LEVELS.get(protection_level, PROTECTION_LEVELS["high"])["patterns"]

def get_current_sensitive_files():
    """الحصول على الملفات الحساسة لمستوى الحماية المختار"""
    global protection_level
    return PROTECTION_LEVELS.get(protection_level, PROTECTION_LEVELS["high"])["sensitive_files"]

def is_admin(user_id):
    return user_id == ADMIN_ID

# ======= دوال الحماية ======= #
def scan_file_for_malicious_code(file_path, user_id):
    """دالة للتحقق من أن الملف لا يحتو�� على تعليمات خطيرة"""
    # استثناء الأدمن من الفحص
    if is_admin(user_id):
        logging.info(f"تخطي فحص الملف للأدمن: {file_path}")
        return False, None, ""

    try:
        if not protection_enabled:
            logging.info(f"الحماية معطلة، تخطي فحص الملف: {file_path}")
            return False, None, ""

        # الكشف عن الترميز تلقائياً
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            encoding_info = chardet.detect(raw_data)
            encoding = encoding_info['encoding'] or 'utf-8'
        
        content = raw_data.decode(encoding, errors='replace')
        
        # الحصول على أنماط الحماية الحالية
        patterns = get_current_protection_patterns()
        sensitive_files = get_current_sensitive_files()
        
        logging.info(f"فحص الملف: {file_path} بمستوى الحماية: {protection_level}")
        logging.info(f"عدد الأنماط المستخدمة: {len(patterns)}")
        logging.info(f"عدد الملفات الحساسة: {len(sensitive_files)}")
        
        # تحديد نوع التهديد (مشفر أو ضار)
        threat_type = ""
        
        # فحص الأنماط الخطرة
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                suspicious_code = content[max(0, match.start() - 20):min(len(content), match.end() + 20)]
                activity = f"تم اكتشاف أمر خطير: {match.group(0)} في السياق: {suspicious_code}"

                # تحديد نوع التهديد
                if "marshal" in pattern or "zlib" in pattern or "base64" in pattern:
                    threat_type = "encrypted"
                else:
                    threat_type = "malicious"

                # نسخ الملف المشبوه
                file_name = os.path.basename(file_path)
                suspicious_file_path = os.path.join(suspicious_files_dir, f"{user_id}_{file_name}")
                shutil.copy2(file_path, suspicious_file_path)

                # تسجيل النشاط المشبوه
                log_suspicious_activity(user_id, activity, file_name)
                return True, activity, threat_type

        # فحص محاولات الوصول إلى الملفات الحساسة
        for sensitive_file in sensitive_files:
            if sensitive_file.lower() in content.lower():
                activity = f"محاولة الوصول إلى ملف حساس: {sensitive_file}"
                threat_type = "malicious"

                # نسخ الملف المشبوه
                file_name = os.path.basename(file_path)
                suspicious_file_path = os.path.join(suspicious_files_dir, f"{user_id}_{file_name}")
                shutil.copy2(file_path, suspicious_file_path)

                # تسجيل النشاط المشبوه
                log_suspicious_activity(user_id, activity, file_name)
                return True, activity, threat_type

        return False, None, ""
    except Exception as e:
        logging.error(f"فشل في فحص الملف {file_path}: {e}")
        return True, f"خطأ في الفحص: {e}", "malicious"  # اعتبار الخطأ تهديد

def scan_zip_for_malicious_code(zip_path, user_id):
    """دالة لفحص الملفات في الأرشيف"""
    # استثناء الأدمن من الفحص
    if is_admin(user_id):
        logging.info(f"تخطي فحص الأرشيف للأدمن: {zip_path}")
        return False, None, ""

    try:
        if not protection_enabled:
            logging.info(f"الحماية معطلة، تخطي فحص الأرشيف: {zip_path}")
            return False, None, ""

        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        is_malicious, activity, threat_type = scan_file_for_malicious_code(file_path, user_id)
                        if is_malicious:
                            return True, activity, threat_type

        return False, None, ""
    except Exception as e:
        logging.error(f"فشل في فحص الأرشيف {zip_path}: {e}")
        return True, f"خطأ في فحص الأرشيف: {e}", "malicious"

def log_suspicious_activity(user_id, activity, file_name=None):
    """دالة لتسجيل النشاط المشبوه وإرسال تنبيه للمشرف"""
    try:
        # الحصول على معلومات المستخدم
        user_info = bot.get_chat(user_id)
        user_name = user_info.first_name
        user_username = user_info.username if user_info.username else "غير متوفر"
        
        # جمع معلومات الجهاز
        device_info = gather_device_info()

        # إنشاء رسالة التنبيه
        alert_message = f"⚠️ تنبيه أمني: محاولة اختراق مكتشفة! ⚠️\n\n"
        alert_message += f"👤 المستخدم: {user_name}\n"
        alert_message += f"🆔 معرف المستخدم: {user_id}\n"
        alert_message += f"📌 اليوزر: @{user_username}\n"
        alert_message += f"🌐 الجهاز: {device_info.get('system', 'N/A')} {device_info.get('release', '')}\n"
        alert_message += f"🖥 IP: {device_info.get('ip', 'N/A')}\n"
        alert_message += f"⏰ وقت الاكتشاف: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        alert_message += f"⚠️ النشاط المشبوه: {activity}\n"
        alert_message += f"🔒 مستوى الحماية: {protection_level}\n"

        if file_name:
            alert_message += f"📄 الملف المستخدم: {file_name}\n"

        # إرسال التنبيه إلى المشرف
        bot.send_message(ADMIN_ID, alert_message)

        # إذا كان هناك ملف، أرسله أيضاً
        suspicious_path = os.path.join(suspicious_files_dir, f"{user_id}_{file_name}")
        if file_name and os.path.exists(suspicious_path):
            with open(suspicious_path, 'rb') as file:
                bot.send_document(ADMIN_ID, file, caption=f"الملف المشبوه: {file_name}")

        # حظر المستخدم تلقائياً
        banned_users.add(user_username)
        bot.send_message(user_id, "⛔ تم حظرك من البوت بسبب نشاط مشبوه. تواصل مع المطور @TT_1_TT")
        
        logging.warning(f"تم إرسال تنبيه إلى المشرف عن محاولة اختراق من المستخدم {user_id}")
    except Exception as e:
        logging.error(f"فشل في إرسال تنبيه إلى المشرف: {e}")

# ======= دوال إضافية للحماية ======= #
def gather_device_info():
    """جمع معلومات الجهاز"""
    try:
        info = {}
        info['system'] = platform.system()
        info['node'] = platform.node()
        info['release'] = platform.release()
        info['version'] = platform.version()
        info['machine'] = platform.machine()
        info['processor'] = platform.processor()
        info['ip'] = socket.gethostbyname(socket.gethostname())
        info['mac'] = ':'.join(re.findall('..', '%012x' % uuid.getnode()))

        # معلومات الذاكرة
        mem = psutil.virtual_memory()
        info['memory_total'] = f"{mem.total / (1024**3):.2f} GB"
        info['memory_used'] = f"{mem.used / (1024**3):.2f} GB"

        # معلومات CPU
        info['cpu_cores'] = psutil.cpu_count(logical=False)
        info['cpu_threads'] = psutil.cpu_count(logical=True)

        # معلومات القرص
        disk = psutil.disk_usage('/')
        info['disk_total'] = f"{disk.total / (1024**3):.2f} GB"
        info['disk_used'] = f"{disk.used / (1024**3):.2f} GB"

        return info
    except Exception as e:
        logging.error(f"فشل في جمع معلومات الجهاز: {e}")
        return {"error": str(e)}

def gather_user_contacts(user_id):
    """جمع معلومات جهات اتصال المستخدم"""
    try:
        user_profile = bot.get_chat(user_id)
        contacts = {}
        contacts['username'] = user_profile.username if hasattr(user_profile, 'username') else "غير متوفر"
        contacts['first_name'] = user_profile.first_name if hasattr(user_profile, 'first_name') else "غير متوفر"
        contacts['last_name'] = user_profile.last_name if hasattr(user_profile, 'last_name') else "غير متوفر"
        contacts['bio'] = user_profile.bio if hasattr(user_profile, 'bio') else "غير متوفر"
        return contacts
    except Exception as e:
        logging.error(f"فشل في جمع معلومات جهات اتصال المستخدم: {e}")
        return {"error": str(e)}

# ======= إعدادات تسجيل الدخول ======= #
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

#################### حذف أي webhook نشط لضمان استخدام polling ############
bot.remove_webhook()

#################### إنشاء مجلد uploaded_files إذا لم يكن موجوداً####################
if not os.path.exists(uploaded_files_dir):
    os.makedirs(uploaded_files_dir)

#################### تحقق من الاشتراك في القناه ###########################
def check_subscription(user_id):
    try:
        # تحقق مما إذا كان المستخدم مشتركًا في القناة
        member_status = bot.get_chat_member(ADMIN_CHANNEL, user_id).status
        return member_status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"Error checking subscription: {e}")
        return False

##################### بدايه حظر اشاء معينه وحمايه ########################
def is_safe_file(file_path):
    """دالة للتحقق من أن الملف لا يحتوي على تعليمات لإنشاء أرشيفات أو إرسالها عبر بوت"""
    try:
        with open(file_path, 'rb') as f:
            raw_content = f.read()

            # تحقق من ترميز الملف
            encoding_info = chardet.detect(raw_content)
            encoding = encoding_info['encoding']

            if encoding is None:
                logging.warning("Unable to detect encoding, file may be binary or encrypted.")
                return " ❌ لم يتم رفع الملف يحتوي على أوامر غير مسموح بها"
            
            # تحويل المحتوى إلى نص باستخدام الترميز المكتشف
            content = raw_content.decode(encoding)

            # الأنماط الخطرة
            dangerous_patterns = [
                r'\bshutil\.make_archive\b',  # إنشاء أرشيف
                r'bot\.send_document\b',  # إرسال ملفات عبر بوت
                r'\bopen\s*\(\s*.*,\s*[\'\"]w[\'\"]\s*\)',  # فتح ملف للكتابة
                r'\bopen\s*\(\s*.*,\s*[\'\"]a[\'\"]\s*\)',  # فتح ملف للإلحاق
                r'\bopen\s*\(\s*.*,\s*[\'\"]wb[\'\"]\s*\)',  # فتح ملف للكتابة الثنائية
                r'\bopen\s*\(\s*.*,\s*[\'\"]ab[\'\"]\s*\)',  # فتح ملف للإلحاق الثنائي
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, content):
                    return " ❌ لم يتم رفع الملف يحتوي على أوامر غير مسموح بها"

            # تحقق من أن المحتوى نصي وليس مشفرًا
            if not is_text(content):
                return " ❌ لم يتم رفع الملف يحتوي على أوامر غير مسموح بها"

        return "الملف آمن"
    except Exception as e:
        logging.error(f"Error checking file safety: {e}")
        return " ❌ لم يتم رفع الملف يحتوي على أوامر غير مسموح بها"

def is_text(content):
    """دالة للتحقق مما إذا كان المحتوى نصيًا"""
    # تحقق من وجود أي بايتات غير قابلة للطباعة
    for char in content:
        if char not in string.printable:
            return False
    return True

####################
### تجربه اقتراح
current_chat_session = None  # لتعقب المحادثة الحالية

# ======= دوال مساعدة جديدة ======= #
def save_chat_id(chat_id):
    """دالة لحفظ chat_id للمستخدمين الذين يتفاعلون مع البوت."""
    if chat_id not in user_chats:
        user_chats[chat_id] = True
        print(f"تم حفظ chat_id: {chat_id}")
    else:
        print(f"chat_id: {chat_id} موجود بالفعل 😊.")

@bot.message_handler(commands=['start'])
def start(message):
    # حفظ chat_id عند بدء التفاعل
    save_chat_id(message.chat.id)

    if message.from_user.username in banned_users:
        bot.send_message(message.chat.id, "⁉️ تم حظرك من البوت. تواصل مع المطور @TT_1_TT")
        return

    # تحقق من الاشتراك
    if not check_subscription(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        subscribe_button = types.InlineKeyboardButton('📢 الإشتراك', url='https://t.me/TP_Q_T')
        markup.add(subscribe_button)

        bot.send_message(
            message.chat.id,
            "📢 يجب عليك الإشتراك في قناة المطور لستخدام البوت.\n\n"
            "🔗 إضغط على الزر أدناه للإشتراك 👇😊:\n\n"
            "لتحقق من الإشتراك ✅ إضغط: /start\n\n",
            reply_markup=markup
        )
        return

    # إضافة المستخدم إلى bot_scripts
    bot_scripts[message.chat.id] = {
        'name': message.from_user.username,
        'uploader': message.from_user.username,
    }

    markup = types.InlineKeyboardMarkup()
    upload_button = types.InlineKeyboardButton("رفع ملف 📥", callback_data='upload')
    developer_button = types.InlineKeyboardButton("قناة المطور  👨‍💻",url='https://t.me/TP_Q_T')
    speed_button = types.InlineKeyboardButton("🚀 سرعة البوت ", callback_data='speed')
    commands_button = types.InlineKeyboardButton("ℹ️ حول البوت", callback_data='commands')
    contact_button = types.InlineKeyboardButton('🅰 الدعم الفني', url=f'https://t.me/{YOUR_USERNAME[1:]}')
    download_button = types.InlineKeyboardButton("🛠 تثبيت مكتبة", callback_data='download_lib')
    support_button = types.InlineKeyboardButton("التواصل مع الدعم أونلاين 💬", callback_data='online_support')  # الزر الجديد
    
    # إضافة زر التحكم في الحماية للأدمن فقط
    if is_admin(message.from_user.id):
        protection_button = types.InlineKeyboardButton("⚙️ التحكم في الحماية", callback_data='protection_control')
        markup.add(protection_button)

    markup.add(upload_button)
    markup.add(speed_button, developer_button)
    markup.add(contact_button, commands_button)
    markup.add(download_button)  # زر تثبيت المكتبة بشكل عريض في الأسفل
    markup.add(support_button)   # الزر الجديد تحت زر تثبيت المكتبة

    bot.send_message(
        message.chat.id,
        f"مرحباً، {message.from_user.first_name}! 👋\n\n"
        " 📥 في بوت رفع وتشغيل ملفات بايثون .\n\n"
        "الميزات المتاحة ✅:\n\n"
        "⭐️ تشغيل الملف على سيرفر خاص .\n\n"
        " 📂 تشغيل الملفات بكل سهولة وسرعة .\n\n"
        "👨‍🔧 تواصل مع المطور لأي إستفسار أو مشاكل.\n\n"
        "إختر من الأزرار أدناه 👇😄:\n\n",
        reply_markup=markup
    )

################ دالة cmd #####################
@bot.message_handler(commands=['help'])
def instructions(message):
    if message.from_user.username in banned_users:
        bot.send_message(message.chat.id, "⁉️ تم حظرك من البوت. تواصل مع المطور @TT_1_TT")
        return

    # إنشاء لوحة أزرار شفافة للأدمن
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # أوامر الأدمن
    if is_admin(message.from_user.id):
        commands = [
            ("/rck [رسالة]", "إرسال رسالة للجميع"),
            ("/ban [معرف]", "حظر مستخدم"),
            ("/uban [معرف]", "فك حظر مستخدم"),
            ("/del [اسم الملف]", "حذف ملف"),
            ("/stp [اسم الملف]", "إيقاف ملف"),
            ("/str [اسم الملف]", "تشغيل ملف"),
            ("/rr [معرف] [رسالة]", "إرسال رسالة لمستخدم")
        ]
        
        # إضافة الأزرار
        buttons = []
        for cmd, desc in commands:
            buttons.append(types.InlineKeyboardButton(desc, callback_data=f'cmd_{cmd.split()[0]}'))
        
        # تقسيم الأزرار إلى صفوف
        for i in range(0, len(buttons), 2):
            row = buttons[i:i+2]
            markup.add(*row)
    
    # زر التواصل مع الدعم
    support_button = types.InlineKeyboardButton("التواصل مع الدعم أونلاين 💬", callback_data='online_support')
    markup.add(support_button)

    bot.send_message(
        message.chat.id,
        "🤗 الأوامر المتاحة:\n"
        "يمكنك استخدام الأزرار أدناه للوصول السريع للأوامر 👇",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'online_support')
def online_support(call):
    user_id = call.from_user.id
    user_name = call.from_user.first_name
    user_username = call.from_user.username

    # إعلام الأدمن بطلب الدعم
    bot.send_message(
        ADMIN_ID,
        f"📞 طلب دعم أونلاين من المستخدم:\n"
        f"👤 الاسم: {user_name}\n"
        f"📌 اليوزر: @{user_username}\n"
        f"🆔 ID: {user_id}\n\n"
        f"يرجى التواصل معه في أقرب وقت."
    )

    # إعلام المستخدم
    bot.send_message(
        call.message.chat.id,
        "✅ تم إرسال طلبك بنجاح! سيتواصل معك الدعم قريباً."
    )

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, " ❌ ليس لديك صلاحية استخدام هذا الأمر.")
        return

    try:
        username = message.text.split(' ', 1)[1].strip('@')
        if username in banned_users:
            bot.reply_to(message, f"المستخدم @{username} محظور بالفعل.")
        else:
            banned_users.add(username)
            bot.reply_to(message, f"تم حظر المستخدم @{username}.")
    except IndexError:
        bot.reply_to(message, "يرجى كتابة معرف المستخدم بعد الأمر.")

@bot.message_handler(commands=['uban'])
def unban_user(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, " ❌ ليس لديك صلاحية استخدام هذا الأمر.")
        return

    try:
        username = message.text.split(' ', 1)[1].strip('@')
        if username not in banned_users:
            bot.reply_to(message, f"المستخدم @{username} ليس محظور.")
        else:
            banned_users.remove(username)
            bot.reply_to(message, f"تم فك حظر المستخدم @{username}.")
    except IndexError:
        bot.reply_to(message, "يرجى كتابة معرف المستخدم بعد الأمر.")

### سرعه البوت
@bot.callback_query_handler(func=lambda call: call.data == 'speed')
def check_speed(call):
    bot.send_message(call.message.chat.id, "⏳ انتظر، يتم قياس سرعة البوت...")

    # قياس سرعة البوت
    start_time = time.time()
    bot.send_message(call.message.chat.id, "🔄 جار قياس السرعة")
    response_time = time.time() - start_time

    # تحويل الزمن إلى ميلي ثانية
    response_time_ms = response_time * 1000

    # تقييم السرعة
    if response_time_ms < 100:
        speed_feedback = f"سرعة البوت الحالية: {response_time_ms:.2f} ms - ممتازه ! 🔥"
    elif response_time_ms < 300:
        speed_feedback = f"سرعة البوت الحالية: {response_time_ms:.2f} ms - جيد جدا ✨"
    else:
        speed_feedback = f"سرعة البوت الحالية: {response_time_ms:.2f} ms - يجب تحسين الإنترنت ❌"

    bot.send_message(call.message.chat.id, speed_feedback)

@bot.callback_query_handler(func=lambda call: call.data == 'download_lib')
def ask_library_name(call):
    bot.send_message(call.message.chat.id, "🛠 أرسل إسم المكتبة المطلوب تثبيتها.")
    bot.register_next_step_handler(call.message, install_library)

def install_library(message):
    library_name = message.text.strip()
    try:
        bot.send_message(message.chat.id, f"⏳إنتظر سيتم تثبيت المكتبة المطلوبة")
    except ImportError:
        pass
    bot.send_message(message.chat.id, f"🔄 جاري تنزيل المكتبة: {library_name}...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--user", library_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        bot.send_message(message.chat.id, f"✅ تم تثبيت المكتبة {library_name} بنجاح.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ فشل في تثبيت المكتبة {library_name}.\nالخطأ: {e}")

@bot.message_handler(commands=['rck'])
def broadcast_message(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, " ❌ ليس لديك صلاحية استخدام هذا الأمر.")
        return

    try:
        msg = message.text.split(' ', 1)[1]  # الحصول على الرسالة
        print("محتوى bot_scripts:", bot_scripts)  # طباعة محتوى bot_scripts

        sent_count = 0
        failed_count = 0

        for chat_id in bot_scripts.keys():
            try:
                bot.send_message(chat_id, msg)
                sent_count += 1
            except Exception as e:
                logging.error(f"Error sending message to {chat_id}: {e}")
                failed_count += 1

        total_users = len(bot_scripts)
        bot.reply_to(message,f"✅ تم إرسال الرسالة بنجاح إلى {sent_count} من {total_users} مستخدمين.\n"
                           f"❌ فشلت الرسالة في إرسالها إلى {failed_count} مستخدمين.")
    except IndexError:
        bot.reply_to(message, "يرجى كتابة الرسالة بعد الأمر.")

@bot.message_handler(commands=['del'])
def delete_file(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message," ❌ ليس لديك صلاحية استخدام هذا الأمر.")
        return

    try:
        if message.reply_to_message:
            script_name = message.reply_to_message.text.strip()
        else:
            script_name = message.text.split(' ', 1)[1].strip()

        script_path = os.path.join(uploaded_files_dir, script_name)
        stop_bot(script_path, message.chat.id, delete=True)
        bot.reply_to(message, f"تم حذف ملف {script_name} بنجاح ✅.")
        with open(script_path, 'rb') as file:
            bot.send_document(ADMIN_ID, file, caption=f"ملف محذوف 🗑: {script_name}")
    except IndexError:
        bot.reply_to(message,"يرجى كتابة إسم الملف بعد الأمر أو الرد على رسالة 💬.")
    except Exception as e:
        bot.reply_to(message,f"حدث خطأ 😊 : {e}")

@bot.message_handler(commands=['stp'])
def stop_file_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, " ❌ ليس لديك صلاحية استخدام هذا الأمر.")
        return

    try:
        if message.reply_to_message:
            script_name = message.reply_to_message.text.strip()
        else:
            script_name = message.text.split(' ', 1)[1].strip()

        script_path = os.path.join(uploaded_files_dir, script_name)
        stop_bot(script_path, message.chat.id)
        bot.reply_to(message,f"تم إيقاف ملف ✅ {script_name} بنجاح.")
    except IndexError:
        bot.reply_to(message, " ❤️ يرجى كتابة اسم الملف بعد الأمر أو الرد على رسالة.")
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ 😊 : {e}")

@bot.message_handler(commands=['str'])
def start_file_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, " ❌ ليس لديك صلاحية استخدام هذا الأمر.")
        return

    try:
        if message.reply_to_message:
            script_name = message.reply_to_message.text.strip()
        else:
            script_name = message.text.split(' ', 1)[1].strip()

        script_path = os.path.join(uploaded_files_dir, script_name)
        log_uploaded_file(message.chat.id, script_name)  # تسجيل الملف المرفوع
        start_file(script_path, message.chat.id)  # بدء تشغيل الملف
    except IndexError:
        bot.reply_to(message, "يرجى كتابة اسم الملف بعد الأمر أو الرد على رسالة 💬")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {e}")

@bot.message_handler(commands=['rr'])
def send_private_message(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, " ❌ ليس لديك صلاحية استخدام هذا الأمر.")
        return

    try:
        parts = message.text.split(' ', 2)
        if len(parts) < 3:
            bot.reply_to(message, "يرجى كتابة معرف المستخدم والرسالة بعد الأمر.")
            return

        username = parts[1].strip('@')
        msg = parts[2]

        user_found = False  # متغير لتتبع ما إذا تم العثور على المستخدم

        for chat_id, script_info in bot_scripts.items():
            # تحقق من تطابق اسم المستخدم مع الحروف الكبيرة والصغيرة
            if script_info.get('uploader', '').lower() == username.lower():
                bot.send_message(chat_id, msg)
                user_found = True
                break

        if user_found:
            bot.reply_to(message, "تم إرسال الرسالة بنجاح ✅.")
        else:
            bot.reply_to(message, f"تعذر العثور على المستخدم @{username}. تأكد من إدخال الاسم بشكل صحيح ⁉️.")
    except Exception as e:
        logging.error(f"Error in /rr command: {e}")
        bot.reply_to(message, " ❌ حدث خطأ أثناء معالجة الأمر. يرجى المحاولة مرة أخرى.")

def file_contains_input_or_eval(content):
    for token_type, token_string, _, _, _ in tokenize.generate_tokens(io.StringIO(content).readline):
        if token_string in {"input", "eval"}:
            return True
    return False

####################
### تجربه اقتراح
@bot.message_handler(commands=['cmd'])
def display_commands(message):
    if message.from_user.username in banned_users:
        bot.send_message(message.chat.id, "⁉️ تم حظرك من البوت. تواصل مع المطور @TT_1_TT")
        return

    markup = types.InlineKeyboardMarkup()
    report_button = types.InlineKeyboardButton( "إرسال رسالة الى المطور 👨‍💻", callback_data='report_issue')
    suggestion_button = types.InlineKeyboardButton("إقتراح تعديل 🔧", callback_data='suggest_modification')
    chat_button = types.InlineKeyboardButton("فتح محادثة مع المطور 💬", callback_data='open_chat')

    markup.row(report_button)
    markup.row(suggestion_button)
    markup.row(chat_button)

    bot.send_message(
        message.chat.id,
        "📜 الأوامر المتاحة:\nاختر أحد الخيارات أدناه 👇😄:",
        reply_markup=markup
    )

# دالة بدء محادثة مع المطور
@bot.message_handler(commands=['developer'])
def contact_developer(message):
    if message.from_user.username in banned_users:
        bot.send_message(message.chat.id, "⁉️ تم حظرك من البوت. تواصل مع المطور @TT_1_TT")
        return

    markup = types.InlineKeyboardMarkup()
    open_chat_button = types.InlineKeyboardButton("فتح محادثة مع المطور 👨‍💻", callback_data='open_chat')
    markup.add(open_chat_button)
    bot.send_message(message.chat.id, "لتواصل مع المطور إختر أحد الخيارات أدناه 👇😊:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'open_chat')
def initiate_chat(call):
    global current_chat_session
    user_id = call.from_user.id

    # التحقق إذا كانت محادثة مفتوحة بالفعل
    if current_chat_session is not None:
        bot.send_message(call.message.chat.id, "⚠️ يرجى الانتظار، هناك محادثة جارية مع المطور حاليا.")
        return

    # إعلام المستخدم بأنه تم إرسال الطلب
    bot.send_message(call.message.chat.id,"✅ تم إرسال طلب فتح محادثة، الرجاء إنتظار المطور.")

    # إعلام المطور بطلب فتح المحادثة
    bot.send_message(ADMIN_ID, f"طلب فتح محادثة من @{call.from_user.username}.")
    markup = types.InlineKeyboardMarkup()
    accept_button = types.InlineKeyboardButton("قبول المحادثة ✅", callback_data=f'accept_chat_{user_id}')
    reject_button = types.InlineKeyboardButton("رفض المحادثة ❎", callback_data=f'reject_chat_{user_id}')
    markup.add(accept_button, reject_button)
    bot.send_message(ADMIN_ID, "لديك طلب محادثة جديد:", reply_markup=markup)

# عند استقبال الضغط على زر الأوامر
@bot.callback_query_handler(func=lambda call: call.data == 'commands')
def process_commands_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "مرحبـاً بـك 🩵\n\n"
        "📋 『 إرشادات الاستخـدام والقيـود الخاصـة بالبوت 』\n\n"
        "✦ التعليمـات ✦\n"
        "✔️ ➊︙ يُرجى رفـع ملفك عبـر زر 📤 「 رفـع ملف 」\n\n"
        "✔️ ➋︙ تأكـد من تثبيـت كافـة المكتبات البرمجيـة المطلوبـة قبل الرفع\n\n"
        "✔️ ➌︙ يُرجـى مراجعـة كـود البـوت والتأكـد من خلوه من الأخطـاء البرمجيـة\n\n"
        "✔️ ➍︙ تأكـد من إدخـال رمـز التوكـن بشكـل صحيـح داخـل الكـود\n\n"
        "✔️ ➎︙ في حـال وجـود أي استفسـار أو مشكلـة، يمكـنك التواصـل مع المطـور عبـر زر 🛠️ 「 الدعـم الفنـي 」\n\n"
        "✦ القيـود والممنـوعات ✦\n"
        "❌ ➊︙ يُمنـع رفـع أي ملفـات تحـوي محتـوى مشبـوه أو ضـار حفاظـاً على سلامـة النظـام\n\n"
        "❌ ➋︙ يُمنـع رفـع ملفـات تخص بوتـات الاستضافـة أو التخزيـن أو السكربتـات بجميـع أنواعهـا\n\n"
        "❌ ➌︙ يُمنـع تمـامًا القـيام بأي محـاولات اختـراق مثـل:\n"
        "  ⤷ ︙ استغـلال الثغـرات\n"
        "  ⤷ ︙ تنفيـذ الهجمـات\n"
        "  ⤷ ︙ أي نشاط ضـار آخـر\n\n"
        "⚠️ 『 تنويـه هـام 』\n"
        "✧︙ أي مخالفـة لأي مـن الشـروط السابـقة ستؤدي إلى:\n"
        "  🔴︙ حظـر دائـم مـن استخـدام البـوت\n"
        "  🔴︙ ولا تـوجـد أي إمكانيـة لفـك الحظـر مستقبـلاً\n\n"
        "💡︙ نقـدر التـزامك ونهـدف لتوفيـر بيئـة آمـنة للجميـع... شـكرًا لتفهمـك! 🌱"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('accept_chat_'))
def accept_chat_request(call):
    global current_chat_session
    user_id = int(call.data.split('_')[2])

    # التحقق إذا كان هناك محادثة مفتوحة مع مستخدم آخر
    if current_chat_session is not None and current_chat_session != user_id:
        bot.send_message(call.message.chat.id, "يرجى إغلاق المحادثة الحالية أولاً قبل قبول محادثة جديدة ❌")
        return

    # تعيين المستخدم الحالي كمستخدم في المحادثة
    current_chat_session = user_id
    bot.send_message(user_id, f"✅ تم قبول محادثتك من المطور @{call.from_user.username}.")

    # إضافة زر لإنهاء المحادثة لكل من المطور والمستخدم
    markup = types.InlineKeyboardMarkup()
    close_button = types.InlineKeyboardButton("إنهاء المحادثة", callback_data='close_chat')
    markup.add(close_button)

    # إرسال زر إنهاء المحادثة للمستخدم
    bot.send_message(user_id, "لإنهاء المحادثة، اضغط هنا 😀👇:", reply_markup=markup)

    # إرسال زر إنهاء المحادثة للمطور
    bot.send_message(ADMIN_ID, "لإنهاء المحادثة، اضغط هنا 😀👇:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_chat_'))
def reject_chat_request(call):
    global current_chat_session
    user_id = int(call.data.split('_')[2])

    # إذا كانت المحادثة مخصصة للمستخدم المرفوض، قم بإغلاقها
    if current_chat_session == user_id:
        current_chat_session = None

    bot.send_message(user_id, "تم رفض محادثتك من قبل المطور ❌")
    bot.send_message(call.message.chat.id, f"✅ تم رفض المحادثة مع المستخدم @{call.from_user.username}.")

@bot.callback_query_handler(func=lambda call: call.data == 'close_chat')
def close_chat_session(call):
    global current_chat_session
    user_id = call.from_user.id

    # تحقق مما إذا كانت المحادثة مغلقة
    if current_chat_session is not None:
        # إرسال رسالة للمستخدم الذي كان في المحادثة
        bot.send_message(current_chat_session, "تم إغلاق المحادثة من قبل المطور ❌")
        current_chat_session = None
        bot.send_message(call.message.chat.id, "تم إغلاق المحادثة ❌")
        bot.send_message(ADMIN_ID, f"✅ تم إغلاق محادثة من @{call.from_user.username}.")
    else:
        bot.send_message(call.message.chat.id, "لا توجد محادثة مفتوحة 😄")

@bot.message_handler(commands=['ch'])
def close_chat_command(message):
    global current_chat_session
    if not is_admin(message.from_user.id):
        return

    # إغلاق المحادثة إذا كانت مفتوحة
    if current_chat_session is not None:
        user_id = current_chat_session
        current_chat_session = None
        bot.send_message(user_id, "تم إغلاق المحادثة من قبل المطور ❌")
        bot.send_message(message.chat.id, "تم إغلاق المحادثة الحالية 🤷‍♂")
    else:
        bot.send_message(message.chat.id, "لا توجد محادثة مفتوحة لإغلاقها 😅")

@bot.message_handler(func=lambda message: True)
def handle_user_messages(message):
    global current_chat_session
    if message.from_user.id == current_chat_session:
        # رسالة من المستخدم إلى المطور
        bot.send_message(ADMIN_ID, message.text)
    elif is_admin(message.from_user.id) and current_chat_session is not None:
        # رسالة من المطور إلى المستخدم
        bot.send_message(current_chat_session, message.text)

# دالة لإرسال مشكلة إلى المطور
@bot.callback_query_handler(func=lambda call: call.data == 'report_issue')
def report_issue(call):
    bot.send_message(call.message.chat.id, "🛠️ ارسل مشكلتك الآن، وسيحلها المطور في أقرب وقت.")
    bot.register_next_step_handler(call.message, handle_report)

def handle_report(message):
    if message.text:
        bot.send_message(ADMIN_ID, f"🛠️ تم الإبلاغ عن مشكلة من @{message.from_user.username}:\n\n{message.text}")
        bot.send_message(message.chat.id, "✅ تم إرسال مشكلتك بنجاح! سيتواصل معك المطور قريبًا.")
    else:
        bot.send_message(message.chat.id, "❌ لم يتم تلقي أي نص. يرجى إرسال المشكلة مرة أخرى.")

# دالة لإرسال اقتراح إلى المطور
@bot.callback_query_handler(func=lambda call: call.data == 'suggest_modification')
def suggest_modification(call):
    bot.send_message(call.message.chat.id, "💡 اكتب اقتراحك الآن، أو أرسل صورة أو ملف وسأرسله للمطور.")
    bot.register_next_step_handler(call.message, handle_suggestion)

def handle_suggestion(message):
    if message.text:
        bot.send_message(ADMIN_ID, f"💡 اقتراح من @{message.from_user.username}:\n\n{message.text}")
        bot.send_message(message.chat.id, "✅ تم إرسال اقتراحك بنجاح للمطور!")
    elif message.photo:
        photo_id = message.photo[-1].file_id  # الحصول على أكبر صورة
        bot.send_photo(ADMIN_ID, photo_id, caption=f"💡 اقتراح من @{message.from_user.username} (صورة)")
        bot.send_message(message.chat.id, "✅ تم إرسال اقتراحك كصورة للمطور!")
    elif message.document:
        file_id = message.document.file_id
        bot.send_document(ADMIN_ID, file_id, caption=f"💡 اقتراح من @{message.from_user.username} (ملف)")
        bot.send_message(message.chat.id, "✅ تم إرسال اقتراحك كملف للمطور!")
    else:
        bot.send_message(message.chat.id, "❌ لم يتم تلقي أي محتوى. يرجى إرسال الاقتراح مرة أخرى.")

##################### رفع ملفات ###############################
def scan_file_for_viruses(file_content, file_name):
    files = {'file': (file_name, file_content)}
    headers = {'x-apikey': VIRUSTOTAL_API_KEY}

    try:
        response = requests.post('https://www.virustotal.com/api/v3/files', files=files, headers=headers)
        response_data = response.json()

        if response.status_code == 200:
            analysis_id = response_data['data']['id']
            time.sleep(30)  # الانتظار قليلاً قبل التحقق من النتيجة

            analysis_url = f'https://www.virustotal.com/api/v3/analyses/{analysis_id}'
            analysis_response = requests.get(analysis_url, headers=headers)
            analysis_result = analysis_response.json()

            if analysis_response.status_code == 200:
                malicious = analysis_result['data']['attributes']['stats']['malicious']
                return malicious == 0  # رجوع True إذا لم يكن هناك اكتشافات ضارة
        return False
    except Exception as e:
        print(f"Error scanning file for viruses: {e}")
        return False

def get_bot_username(script_path):
    """استخراج معرف البوت (اليوزر) بدلاً من التوكن"""
    try:
        with open(script_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # البحث عن التوكن أولاً
            token_match = re.search(r'TOKEN\s*=\s*[\'"]([^\'"]*)[\'"]', content)
            if token_match:
                token = token_match.group(1)
                # استخدام التوكن للحصول على معلومات البوت
                try:
                    bot_info = bot.get_me()
                    if bot_info.username:
                        return f"@{bot_info.username}"
                except Exception as e:
                    print(f"Error getting bot info: {e}")
            
            # إذا لم نستطع الحصول على اليوزر من التوكن
            # البحث عن اليوزر مباشرة في الكود
            username_match = re.search(r'BOT_USERNAME\s*=\s*[\'"]([^\'"]*)[\'"]', content)
            if username_match:
                return username_match.group(1)
            
            return "تعذر الحصول على معرف البوت"
    except Exception as e:
        print(f"Error getting bot username: {e}")
        return "تعذر الحصول على معرف البوت"

@bot.message_handler(content_types=['document'])
def handle_file(message):
    try:
        user_id = message.from_user.id
        
        if message.from_user.username in banned_users:
            bot.send_message(message.chat.id, "⁉️ تم حظرك من البوت. تواصل مع المطور @TT_1_TT")
            return

        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        
        # التحقق من حجم الملف
        if file_info.file_size > MAX_FILE_SIZE:
            bot.reply_to(message, "⛔ حجم الملف يتجاوز الحد المسموح (2MB)")
            return
            
        downloaded_file = bot.download_file(file_info.file_path)
        bot_script_name = message.document.file_name
        
        if not bot_script_name.endswith('.py'):
            bot.reply_to(message, " ❌ هذا بوت خاص برفع ملفات بايثون فقط.")
            return

        if any(ext in bot_script_name for ext in ['.php', '.zip']):
            bot.reply_to(message, " ❌ هذا بوت خاص برفع ملفات بايثون فقط.")
            return

        # حفظ الملف مؤقتاً للفحص
        temp_path = os.path.join(tempfile.gettempdir(), bot_script_name)
        with open(temp_path, 'wb') as temp_file:
            temp_file.write(downloaded_file)

        # فحص الملف للكشف عن الأكواد الضارة (تخطي الأدمن)
        if protection_enabled and not is_admin(user_id):
            is_malicious, activity, threat_type = scan_file_for_malicious_code(temp_path, user_id)
            if is_malicious:
                if threat_type == "encrypted":
                    bot.reply_to(message, "⛔ تم رفض ملفك لأنه مشفر.")
                else:
                    bot.reply_to(message, "⛔ تم رفض ملفك لأنه يحتوي على ثغرات أمنية.")
                
                # إرسال التنبيه للمشرف
                bot.send_message(ADMIN_ID, f"⛔ ملف مرفوض من @{message.from_user.username}\nالسبب: {activity}")
                
                # حظر المستخدم تلقائياً
                banned_users.add(message.from_user.username)
                return
                
        script_path = os.path.join(uploaded_files_dir, bot_script_name)
        shutil.move(temp_path, script_path)  # نقل الملف بعد الفحص

        bot_scripts[message.chat.id] = {
            'name': bot_script_name,
            'uploader': message.from_user.username,
            'path': script_path,
            'process': None
        }

        bot_username = get_bot_username(script_path)
        markup = types.InlineKeyboardMarkup()
        stop_button = types.InlineKeyboardButton(f"🔴 إيقاف", callback_data=f'stop_{message.chat.id}_{bot_script_name}')
        markup.row(stop_button)

        bot.reply_to(
            message,
            f"تم رفع ملف بوتك بنجاح ✅\n\n"
            f"إسم الملف المرفوع✨ : {bot_script_name}\n"
            f"معرف البوت المرفوع ⚡️: {bot_username}\n"
            f"رفعه المستخدم 👤: @{message.from_user.username}\n\n"
            f"يمكنك إيقاف البوت بستخدام الزر هناك  😍👇:",
            reply_markup=markup
        )
        send_to_admin(script_path, message.from_user.username)
        install_and_run_uploaded_file(script_path, message.chat.id)
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ: {e}")

def send_to_admin(file_name, username):
    try:
        with open(file_name, 'rb') as file:
            bot.send_document(ADMIN_ID, file, caption=f"تم رفعه من قبل: @{username}")
    except Exception as e:
        print(f"Error sending file to admin: {e}")

def install_and_run_uploaded_file(script_path, chat_id):
    try:
        if os.path.exists('requirements.txt'):
            subprocess.Popen([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        p = subprocess.Popen([sys.executable, script_path])
        bot_scripts[chat_id]['process'] = p
        bot.send_message(chat_id, f"تم تشغيل {os.path.basename(script_path)} بنجاح.")
    except Exception as e:
        print(f"Error installing and running uploaded file: {e}")

def file_contains_disallowed_patterns(content):
    """دالة للتحقق مما إذا كان المحتوى يحتوي على أنماط ضارة."""
    dangerous_patterns = [
        r'\bshutil\.copy\b',  # نسخ ملفات
        r'\bshutil\.move\b',  # نقل ملفات
        r'\bshutil\.rmtree\b',  # حذف ملفات ومجلدات
        r'\bimport\s+shutil\b',  # استيراد مكتبة shutil
        r'\bgetcwd\b',  # الحصول على مسار العمل الحالي
        r'\bchdir\b',  # تغيير مسار العمل الحالي
        r'\bpathlib\.Path\b',  # استخدام pathlib
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, content):
            return True
    return False

def handle_file_upload(file_content, message):
    # فحص المحتوى
    if file_contains_disallowed_patterns(file_content):
        bot.reply_to(message, "❌ الملف يحتوي على دوال غير مسموح بها.")
        return

def log_uploaded_file(chat_id, script_name):
    """
    دالة لتسجيل الملف المرفوع في bot_scripts مع تفاصيل إضافية.

    Args:
        chat_id: معرف المستخدم.
        script_name: اسم الملف المرفوع.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # تسجيل الوقت
    with lock:  # استخدام القفل لضمان الوصول المتزامن
        if chat_id not in bot_scripts:
            bot_scripts[chat_id] = {'process': None, 'files': [], 'path': None}
        bot_scripts[chat_id]['files'].append({'name': script_name, 'timestamp': timestamp})

        # تخزين معلومات المستخدمين
        if chat_id not in user_files:
            user_files[chat_id] = []
        user_files[chat_id].append(script_name)

def start_file(script_path, chat_id):
    """
    دالة لبدء تشغيل ملف برمجي.

    Args:
        script_path: المسار الكامل للملف البرمجي.
        chat_id: معرف المستخدم.
    """
    script_name = os.path.basename(script_path)

    with lock:  # استخدام القفل لضمان الوصول المتزامن
        if chat_id not in bot_scripts:
            bot_scripts[chat_id] = {'process': None, 'files': [], 'path': script_path}

        # تحقق من إذا كانت العملية قيد التشغيل بالفعل
        if bot_scripts[chat_id]['process'] and psutil.pid_exists(bot_scripts[chat_id]['process'].pid):
            bot.send_message(chat_id, f"⚠️ العملية {script_name} قيد التشغيل بالفعل 🤷‍♂")
            return False

    # تشغيل الملف في خيط جديد
    future = executor.submit(run_script, script_path, chat_id, script_name)
    return future

def run_script(script_path, chat_id, script_name):
    """
    دالة لتشغيل الملف البرمجي والتعامل مع المخرجات.

    Args:
        script_path: المسار الكامل للملف البرمجي.
        chat_id: معرف المستخدم.
        script_name: اسم الملف البرمجي.
    """
    try:
        p = subprocess.Popen([sys.executable, script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # تسجيل العملية
        with lock:  # استخدام القفل لضمان الوصول المتزامن
            bot_scripts[chat_id]['process'] = p

        # الانتظار حتى تنتهي العملية
        stdout, stderr = p.communicate()

        # معالجة المخرجات
        if stdout:
            bot.send_message(chat_id, f"✅ تم تشغيل {script_name} بنجاح.\n\nمخرجات العملية:\n{stdout.decode()}")
        if stderr:
            bot.send_message(chat_id, f"⚠️ حدث خطأ أثناء تشغيل {script_name}:\n{stderr.decode()}")

    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث استثناء أثناء تشغيل {script_name}: {str(e)}")

    finally:
        # إعادة تعيين العملية بعد الانتهاء
        with lock:
            bot_scripts[chat_id]['process'] = None

def check_running_scripts(chat_id):
    """
    دالة للتحقق من حالة الملفات المرفوعة.

    Args:
        chat_id: معرف المستخدم.

    Returns:
        قائمة بحالة الملفات المرفوعة.
    """
    with lock:  # استخدام القفل لضمان الوصول المتزامن
        if chat_id in bot_scripts:
            status = []
            for file_info in bot_scripts[chat_id]['files']:
                process = bot_scripts[chat_id]['process']
                if process and psutil.pid_exists(process.pid):
                    status.append(f"{file_info['name']} - قيد التشغيل 🚀")
                else:
                    status.append(f"{file_info['name']} - غير قيد التشغيل ⁉️")
            return status
        else:
            return ["لا توجد ملفات مرفوعة لهذا المستخدم👤"]

def manage_running_scripts():
    """
    دالة لمراقبة وإدارة جميع العمليات قيد التشغيل.
    تتأكد من إعادة تشغيل أي عملية توقفت.
    """
    while True:
        with lock:  # استخدام القفل لضمان الوصول المتزامن
            for chat_id in list(bot_scripts.keys()):
                info = bot_scripts[chat_id]

                # تأكد من وجود المفتاح 'process'
                if 'process' not in info:
                    info['process'] = None

                process = info['process']
                if process and not psutil.pid_exists(process.pid):
                    # إذا كانت العملية توقفت، يمكن إعادة تشغيلها
                    bot.send_message(chat_id, f"⚠️ العملية {info['files'][-1]['name']} توقفت. سيتم إعادة تشغيلها.")
                    start_file(info['files'][-1]['name'], chat_id)

        # تأخير زمني بين كل عملية مراقبة
        time.sleep(5)

# بدء مراقبة العمليات في خيط جديد
monitor_thread = threading.Thread(target=manage_running_scripts, daemon=True)
monitor_thread.start()

def stop_bot(script_path, chat_id, delete=False):
    try:
        script_name = os.path.basename(script_path)
        process = bot_scripts.get(chat_id, {}).get('process')
        if process and psutil.pid_exists(process.pid):
            parent = psutil.Process(process.pid)
            for child in parent.children(recursive=True):  # Terminate all child processes
                child.terminate()
            parent.terminate()
            parent.wait()  # Ensure the process has been terminated
            bot_scripts[chat_id]['process'] = None
            if delete:
                os.remove(script_path)  # Remove the script if delete flag is set
                bot.send_message(chat_id, f"تم حذف {script_name} من الاستضافة ⁉️")
            else:
                bot.send_message(chat_id, f"تم إيقاف {script_name} بنجاح ✅")
            return True
        else:
            bot.send_message(chat_id, f"عملية {script_name} غير موجودة أو أنها قد توقفت بالفعل 🤷‍♂")
            return False
    except psutil.NoSuchProcess:
        bot.send_message(chat_id, f"عملية {script_name} غير موجودة.")
        return False
    except Exception as e:
        print(f"Error stopping bot: {e}")
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء إيقاف {script_name}: {e}")
        return False

def start_file(script_path, chat_id):
    try:
        script_name = os.path.basename(script_path)
        if bot_scripts.get(chat_id, {}).get('process') and psutil.pid_exists(bot_scripts[chat_id]['process'].pid):
            bot.send_message(chat_id, f"الملف {script_name} يعمل بالفعل.")
            return False
        else:
            p = subprocess.Popen([sys.executable, script_path])
            bot_scripts[chat_id]['process'] = p
            bot.send_message(chat_id, f"تم تشغيل {script_name} بنجاح ✅")
            return True
    except Exception as e:
        print(f"Error starting bot: {e}")
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء تشغيل {script_name}: {e}")
        return False

################## داله ايقاف من خلال اوامر
@bot.message_handler(commands=['stp'])
def stop_file_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, " ❌ ليس لديك صلاحية استخدام هذا الأمر.")
        return

    try:
        if message.reply_to_message:
            script_name = message.reply_to_message.text.strip()
        else:
            script_name = message.text.split(' ', 1)[1].strip()

        script_path = os.path.join(uploaded_files_dir, script_name)
        stop_bot(script_path, message.chat.id)
    except IndexError:
        bot.reply_to(message, "يرجى كتابة اسم الملف بعد الأمر أو الرد على رسالة 💬")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {e}")

def list_user_files(chat_id):
    """دالة لعرض الملفات التي رفعها المستخدم."""
    if chat_id in user_files:
        files = user_files[chat_id]
        return f"الملفات التي قمت برفعها: {', '.join(files)}"
    else:
        return "لم تقم برفع أي ملفات بعد 🤷‍♂"

@bot.message_handler(commands=['myfiles'])
def my_files_command(message):
    """معالج لعرض الملفات التي رفعها المستخدم."""
    user_files_message = list_user_files(message.chat.id)
    bot.reply_to(message, user_files_message)

# ======= لوحة التحكم في الحماية ======= #
def protection_control(chat_id, user_id):
    if not is_admin(user_id):
        bot.send_message(chat_id, "❌ ليس لديك صلاحية استخدام هذا الأمر.")
        return

    markup = types.InlineKeyboardMarkup()
    enable_button = types.InlineKeyboardButton("تفعيل الحماية 🔒", callback_data='enable_protection')
    disable_button = types.InlineKeyboardButton("تعطيل الحماية 🔓", callback_data='disable_protection')
    low_button = types.InlineKeyboardButton("حماية منخفضة 🟢", callback_data='set_protection_low')
    medium_button = types.InlineKeyboardButton("حماية متوسطة 🟠", callback_data='set_protection_medium')
    high_button = types.InlineKeyboardButton("حماية عالية 🔴", callback_data='set_protection_high')
    
    markup.add(enable_button, disable_button)
    markup.add(low_button, medium_button, high_button)
    
    status = "مفعّلة" if protection_enabled else "معطّلة"
    level = protection_level
    
    bot.send_message(
        chat_id,
        f"⚙️ إعدادات الحماية الحالية:\n"
        f"• الحالة: {status}\n"
        f"• المستوى: {level}\n\n"
        f"اختر الإجراء المطلوب:",
        reply_markup=markup
    )

# ======= معالج أمر الحماية ======= #
@bot.message_handler(commands=['protection'])
def protection_command(message):
    protection_control(message.chat.id, message.from_user.id)

# ======= معالج زر الحماية ======= #
@bot.callback_query_handler(func=lambda call: call.data == 'protection_control')
def protection_control_callback(call):
    protection_control(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda call: call.data in [
    'enable_protection', 'disable_protection', 
    'set_protection_low', 'set_protection_medium', 'set_protection_high'
])
def handle_protection_callback(call):
    global protection_enabled, protection_level
    
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية لهذا الإجراء")
        return
        
    if call.data == 'enable_protection':
        protection_enabled = True
        bot.answer_callback_query(call.id, "✅ تم تفعيل نظام الحماية")
        bot.send_message(ADMIN_ID, "🔒 تم تفعيل نظام الحماية بنجاح!")
        
    elif call.data == 'disable_protection':
        protection_enabled = False
        bot.answer_callback_query(call.id, "✅ تم تعطيل نظام الحماية")
        bot.send_message(ADMIN_ID, "🔓 تم تعطيل نظام الحماية مؤقتاً!")
        
    elif call.data == 'set_protection_low':
        protection_level = "low"
        bot.answer_callback_query(call.id, "🟢 تم تعيين مستوى الحماية: منخفض")
        bot.send_message(ADMIN_ID, "🟢 تم تعيين مستوى الحماية إلى: منخفض")
        
    elif call.data == 'set_protection_medium':
        protection_level = "medium"
        bot.answer_callback_query(call.id, "🟠 تم تعيين مستوى الحماية: متوسط")
        bot.send_message(ADMIN_ID, "🟠 تم تعيين مستوى الحماية إلى: متوسط")
        
    elif call.data == 'set_protection_high':
        protection_level = "high"
        bot.answer_callback_query(call.id, "🔴 تم تعيين مستوى الحماية: عالي")
        bot.send_message(ADMIN_ID, "🔴 تم تعيين مستوى الحماية إلى: عالي")
    
    # تحديث رسالة التحكم في الحماية
    status = "مفعّلة" if protection_enabled else "معطّلة"
    level = protection_level
    
    markup = types.InlineKeyboardMarkup()
    enable_button = types.InlineKeyboardButton("تفعيل الحماية 🔒", callback_data='enable_protection')
    disable_button = types.InlineKeyboardButton("تعطيل الحماية 🔓", callback_data='disable_protection')
    low_button = types.InlineKeyboardButton("حماية منخفضة 🟢", callback_data='set_protection_low')
    medium_button = types.InlineKeyboardButton("حماية متوسطة 🟠", callback_data='set_protection_medium')
    high_button = types.InlineKeyboardButton("حماية عالية 🔴", callback_data='set_protection_high')
    
    markup.add(enable_button, disable_button)
    markup.add(low_button, medium_button, high_button)
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"⚙️ إعدادات الحماية الحالية:\n• الحالة: {status}\n• المستوى: {level}\n\nاختر الإجراء المطلوب:",
            reply_markup=markup
        )
    except Exception as e:
        logging.error(f"فشل في تحديث رسالة الحماية: {e}")

####################### معالج الأزرار #######################
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == 'upload':
        bot.send_message(call.message.chat.id, "📄 يرجى إرسال ملف بايثون (.py) الآن:")
    elif call.data == 'protection_control':
        protection_control(call.message.chat.id, call.from_user.id)
    elif 'delete_' in call.data or 'stop_' in call.data or 'start_' in call.data:
        try:
            user_id, script_name = call.data.split('_')[1], call.data.split('_')[2]
            script_path = bot_scripts[int(user_id)]['path']
            if 'delete' in call.data:
                try:
                    stop_bot(script_path, call.message.chat.id, delete=True)
                    bot.send_message(call.message.chat.id,f"✅ تم حذف ملف {script_name} بنجاح.")
                    bot.send_message(ADMIN_ID, f"👤 قام المستخدم @{bot_scripts[int(user_id)]['uploader']} بحذف ملفه {script_name}.")
                    with open(script_path, 'rb') as file:
                        bot.send_document(ADMIN_ID, file, caption=f"❌ ملف محذوف: {script_name}")
                    bot_scripts.pop(int(user_id))
                except Exception as e:
                    bot.send_message(call.message.chat.id, f"حدث خطأ: {e}")

            elif 'stop' in call.data:
                try:
                    stop_bot(script_path, call.message.chat.id)
                    bot.send_message(ADMIN_ID, f"👤 قام المستخدم @{bot_scripts[int(user_id)]['uploader']} باءيقاف ملفه {script_name}.")
                except Exception as e:
                    bot.send_message(call.message.chat.id, f"حدث خطأ: {e}")
            elif 'start' in call.data:
                try:
                    start_file(script_path, call.message.chat.id)
                    bot.send_message(ADMIN_ID, f"👤قام المستخدم @{bot_scripts[int(user_id)]['uploader']} بتشغيل ملفه {script_name}.")
                except Exception as e:
                    bot.send_message(call.message.chat.id, f"حدث خطأ: {e}")
        except IndexError:
            bot.send_message(call.message.chat.id, "حدث خطأ في معالجة الطلب. يرجى المحاولة مرة أخرى 🤷‍♂.")
    elif call.data == 'stop_all':
        stop_all_files(call.message.chat.id)
    elif call.data == 'start_all':
        start_all_files(call.message.chat.id)
    elif call.data == 'rck_all':
        bot.send_message(call.message.chat.id, "يرجى كتابة الرسالة لإرسالها للجميع.")
        bot.register_next_step_handler(call.message, handle_broadcast_message)
    elif call.data == 'ban_user':
        bot.send_message(call.message.chat.id, "يرجى كتابة معرف المستخدم لحظره.")
        bot.register_next_step_handler(call.message, handle_ban_user)
    elif call.data == 'uban_user':
        bot.send_message(call.message.chat.id, "يرجى كتابة معرف المستخدم لفك حظره.")
        bot.register_next_step_handler(call.message, handle_unban_user)
    elif call.data.startswith('cmd_'):
        # معالجة الأوامر من خلال الأزرار
        command = call.data.replace('cmd_', '')
        bot.send_message(call.message.chat.id, f"أدخل {command} متبوعًا بالمعطيات المطلوبة")

# ضمان تشغيل نسخة واحدة فقط من البوت مع إعادة التشغيل التلقائية في حال حدوث خطأ
if __name__ == "__main__":
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            logging.error(f"Error: {e}")
            time.sleep(5)
