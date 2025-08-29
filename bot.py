import os
import json
import logging
import requests
from io import BytesIO
from bs4 import BeautifulSoup
import psutil
from telegram import InputMediaDocument, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from user2_layout import (
    generate_html_with_answers as generate_html_with_answers_user2,
    generate_html_only_questions as generate_html_only_questions_user2,
    generate_answer_key_table as generate_answer_key_table_user2
)
import re
from html import unescape
from datetime import datetime, timezone, timedelta

# === CONFIG ===
BOT_TOKEN = "7719606789:AAFYmaHQ0bok6xLp_nQvpxRuoq5UfgLH6o4"
OWNER_IDS = {8493360284}  # Bot owners
AUTHORIZED_USER_IDS = set(OWNER_IDS)
PLAN = "PRO PLAN⚡"

ASK_NID = 0
extracted_papers_count = 0

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== Helper Functions ====================
def is_authorized(user_id):
    return user_id in AUTHORIZED_USER_IDS or user_id in OWNER_IDS

async def send_unauthorized_message(update: Update):
    if update.message:
        await update.message.reply_text("❌ Access Denied. You are not authorized to use this bot.")
    elif update.callback_query:
        await update.callback_query.answer("❌ Access Denied!", show_alert=True)

def escape_markdown(text):
    if not text:
        return ""
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', str(text))

def unix_to_ist(unix_timestamp):
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.fromtimestamp(unix_timestamp, ist).strftime("%d %B %Y, %I:%M %p")

def clean_html(html):
    return BeautifulSoup(html or "", "html.parser").get_text(separator="\n", strip=True)

def extract_syllabus(description):
    soup = BeautifulSoup(description, 'html.parser')
    lines = soup.get_text(separator="\n").splitlines()
    subjects = {"Physics": "", "Chemistry": "", "Mathematics": ""}
    for line in lines:
        if "Physics" in line:
            subjects["Physics"] = line.replace("Physics :", "").strip()
        elif "Chemistry" in line:
            subjects["Chemistry"] = line.replace("Chemistry :", "").strip()
        elif "Mathematics" in line:
            subjects["Mathematics"] = line.replace("Mathematics :", "").strip()
    return subjects

def fetch_locale_json_from_api(nid, prefer_lang="843"):
    url = f"https://learn.aakashitutor.com/quiz/{nid}/getlocalequestions"
    try:
        response = requests.get(url, timeout=50)
        response.raise_for_status()
        raw = response.json()
        out = []

        for block in raw.values():
            # Try preferred language (default = English / 843)
            content = block.get(prefer_lang)

            # Fallback: if preferred language not found, take first available
            if not content:
                for _, c in block.items():
                    if isinstance(c, dict) and "body" in c:
                        content = c
                        break

            if content and "body" in content:
                out.append({
                    "body": content.get("body", ""),
                    "alternatives": content.get("alternatives", []),
                    "solution": content.get("solution", {}),
                    "language": content.get("language_names", ["Unknown"])[0]
                })

        return out if out else None
    except Exception as e:
        print(f"[ERROR fetching {nid}] {e}")
        return None

def fetch_test_title_and_description(nid):
    url = f"https://learn.aakashitutor.com/api/getquizfromid?nid={nid}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data:
            return data[0].get("title", f"Test_{nid}"), data[0].get("description", "")
    except:
        pass
    return f"Test_{nid}", ""

def process_html_content(html):
    if not html:
        return ""
    soup = BeautifulSoup(html, 'html.parser')
    for img in soup.find_all('img'):
        src = img.get('src')
        if src and src.startswith('//'):
            img['src'] = f"https:{src}"
    return str(soup)

# ==================== Command Handlers ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await send_unauthorized_message(update)
        return

    await update.message.reply_text(
        """🤖 *Aakash Extractor Bot*

Commands:
• `/extract` - Extracts and sends all 3 HTML formats for a given NID.
• `/status` - Shows bot status, usage, and plan.
• `/info <code>` Gives info about Test title/Display name/syllabus etc.
""",
        parse_mode='Markdown'
    )

async def authorize_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        await update.message.reply_text("🚫 Only the bot owner can use this command.")
        return

    try:
        user_id = int(context.args[0])
        global AUTHORIZED_USER_IDS
        AUTHORIZED_USER_IDS.add(user_id)
        await update.message.reply_text(f"✅ User ID {user_id} authorized.")
    except:
        await update.message.reply_text("❌ Invalid usage. Example: /au 123456789")

async def revoke_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        await update.message.reply_text("🚫 Only the bot owner can use this command.")
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text("❌ Invalid usage. Example: /ru 123456789")
        return

    try:
        user_id = int(context.args[0])
        if user_id in OWNER_IDS:
            await update.message.reply_text("🚫 You cannot revoke yourself.")
            return

        global AUTHORIZED_USER_IDS
        AUTHORIZED_USER_IDS.discard(user_id)
        await update.message.reply_text(f"🗑️ User ID {user_id} revoked successfully.")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Example: /ru 123456789")


# ==================== /send Command ====================
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        await update.message.reply_text("🚫 Only the bot owner can use this command.")
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text("❌ Please provide a CODE. Example: /send 4382000229")
        return

    code = context.args[0]
    global AUTHORIZED_USER_IDS
    all_users = AUTHORIZED_USER_IDS

    if not all_users:
        await update.message.reply_text("⚠️ No authorized users to send to.")
        return

    msg = f"👋 Hey there! Here is an extraction code:\n`{code}`"
    success = 0
    fail = 0

    for uid in all_users:
        try:
            await context.bot.send_message(chat_id=uid, text=msg, parse_mode="Markdown")
            success += 1
        except Exception as e:
            print(f"Failed to send to {uid}: {e}")
            fail += 1

    await update.message.reply_text(f"📤 Sent to {success} user(s). ❌ Failed for {fail} user(s).")



async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await send_unauthorized_message(update)
        return

    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    msg = f"""📊 *Bot Status*

📄 Extracted Papers: *{extracted_papers_count}*
🧠 CPU Usage: *{cpu}%*
💾 RAM Usage: *{ram.percent}%*
👥 Authorized Users: *{len(AUTHORIZED_USER_IDS)}*
🪪 Plan: *{PLAN}*
👑 Owner: *Linuxx*
"""
    await update.message.reply_text(msg, parse_mode='Markdown')

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await send_unauthorized_message(update)
        return

    if not context.args:
        await update.message.reply_text("❌ Please provide a CODE. Example: /info 4382000229")
        return

    nid = context.args[0]
    try:
        url = f"https://learn.aakashitutor.com/api/getquizfromid?nid={nid}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data or not isinstance(data, list):
            raise ValueError("Invalid response format")

        quiz = data[0]
        title = quiz.get("title", "N/A")
        display_name = quiz.get("display_name", "N/A")
        raw_description = quiz.get("description", "")
        quiz_open = quiz.get("quiz_open")
        quiz_close = quiz.get("quiz_close")

        test_open = unix_to_ist(int(quiz_open)) if quiz_open else "N/A"
        test_close = unix_to_ist(int(quiz_close)) if quiz_close else "N/A"

        msg = f"*📘 CODE Info*\n\n"
        msg += f"*📝 Title:* {escape_markdown(title)}\n"
        msg += f"*📛 Display Name:* {escape_markdown(display_name)}\n"
        msg += f"*🟢 Test Opens:* {escape_markdown(test_open)}\n"
        msg += f"*🔴 Test Closes:* {escape_markdown(test_close)}\n\n"

        decoded = unescape(raw_description or "")
        matches = re.findall(r'<strong>([^<:]+)\s*:\s*</strong>(.*?)<br>', decoded, re.IGNORECASE)

        if not matches:
            msg += "*📚 Syllabus:*\n>>> Not on Server"
        else:
            for subject, content in matches:
                subject_md = escape_markdown(subject.strip())
                content_md = escape_markdown(content.strip())
                msg += f"*{subject_md}*\n>>> {content_md}\n\n"

        await update.message.reply_text(msg.strip(), parse_mode="MarkdownV2")

    except Exception as e:
        logging.error(f"Error fetching info for NID {nid}: {e}")
        await update.message.reply_text(f"❌ Failed to fetch info for CODE {nid}.")

async def extract_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await send_unauthorized_message(update)
        return ConversationHandler.END

    await update.message.reply_text("🔢 Please send the CODE to extract:")
    return ASK_NID

async def handle_nid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global extracted_papers_count
    nid = update.message.text.strip()

    if not nid.isdigit():
        await update.message.reply_text("❌ Invalid CODE. Please Recheck.")
        return ASK_NID

    await update.message.reply_text("🔍 Extracting data and generating HTMLs...")

    # Fetch data
    data = fetch_locale_json_from_api(nid)
    if not data:
        await update.message.reply_text("⚠️ No valid data found for this CODE.")
        return ConversationHandler.END

    # Fetch test title and description
    title, desc = fetch_test_title_and_description(nid)

    user_id = update.effective_user.id

    if user_id == 7138086137:  # Harsh's ID
        htmls = {
            "QP_with_Answers.html": generate_html_with_answers_user2(data, title, desc),
            "Only_Answer_Key.html": generate_answer_key_table_user2(data, title, desc),
            "Only_Question_Paper.html": generate_html_only_questions_user2(data, title, desc)
        }
    else:
        htmls = {
            "QP_with_Answers.html": generate_html_with_answers(data, title, desc),
            "Only_Answer_Key.html": generate_answer_key_table(data, title, desc),
            "Only_Question_Paper.html": generate_html_only_questions(data, title, desc)
        }

    # Prepare documents to send
    docs = []
    for filename, html in htmls.items():
        bio = BytesIO(html.encode("utf-8"))
        bio.name = filename
        docs.append(bio)

    # Send all HTML files as a media group
    await update.message.reply_media_group(
        [InputMediaDocument(media=doc, filename=doc.name) for doc in docs]
    )

    extracted_papers_count += 1
    await update.message.reply_text("✅ All HTML files sent!")

    return ConversationHandler.END


# === Utility Functions ===
def fetch_locale_json_from_api(nid):
    url = f"https://learn.aakashitutor.com/quiz/{nid}/getlocalequestions"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        raw = response.json()
        out = []
        for block in raw.values():
            english = block.get("843")
            if english and "body" in english:
                out.append({
                    "body": english["body"],
                    "alternatives": english.get("alternatives", [])
                })
        return out
    except:
        return None

def fetch_test_title_and_description(nid):
    url = f"https://learn.aakashitutor.com/api/getquizfromid?nid={nid}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data:
            return data[0].get("title", f"Test_{nid}"), data[0].get("description", "")
    except:
        pass
    return f"Test_{nid}", ""

def process_html_content(html):
    if not html:
        return ""
    soup = BeautifulSoup(html, 'html.parser')
    for img in soup.find_all('img'):
        src = img.get('src')
        if src and src.startswith('//'):
            img['src'] = f"https:{src}"
    return str(soup)

# === HTML Generators - Modern Premium Theme ===
def generate_html_with_answers(data, test_title, syllabus):
    """Generate HTML with questions and highlighted correct answers - Simple Vibrant Layout"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<title>{test_title}</title>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;600;700&display=swap');
    
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    
    body {{
        font-family: 'Roboto', sans-serif;
        background: #f0f4f8;
        color: #2d3748;
        padding: 40px 20px;
        line-height: 1.6;
        min-height: 100vh;
    }}

    .container {{
        max-width: 1000px;
        margin: 0 auto;
    }}

    table {{
        border-collapse: collapse;
        width: 100%;
        margin: 30px 0;
        background: #ffffff;
    }}
    
    table, th, td {{
        border: 1px solid #e2e8f0;
        padding: 15px;
        text-align: center;
    }}
    
    th {{
        background: #3182ce;
        color: white;
        font-weight: 600;
    }}
    
    .header {{
        text-align: center;
        margin-bottom: 50px;
        padding: 50px 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }}
    
    .header h1 {{
        font-size: 42px;
        font-weight: 700;
        margin: 0;
    }}
    
    .question-section {{
        margin-bottom: 40px;
        padding: 30px 0;
        border-bottom: 3px solid #e2e8f0;
    }}
    
    .question-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 25px;
    }}
    
    .question-number {{
        background: #3182ce;
        color: white;
        padding: 12px 24px;
        font-size: 18px;
        font-weight: 700;
        border-radius: 6px;
    }}
    
    .watermark {{
        background: #e53e3e;
        color: white;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 600;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .watermark a {{
        color: white;
        text-decoration: none;
    }}
    
    .question-text {{
        font-size: 18px;
        margin-bottom: 30px;
        color: #4a5568;
        line-height: 1.7;
    }}
    
    .options-container {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin-top: 25px;
    }}
    
    .option {{
        padding: 20px;
        font-size: 16px;
        color: #2d3748;
        border: 2px solid #cbd5e0;
        background: #f7fafc;
        transition: all 0.2s ease;
    }}
    
    .option:hover {{
        border-color: #3182ce;
        background: #edf2f7;
    }}
    
    .option.correct {{
        background: #38a169;
        border-color: #38a169;
        color: white;
        font-weight: 600;
        position: relative;
    }}
    
    .option.correct::after {{
        content: '✓';
        position: absolute;
        top: 15px;
        right: 20px;
        font-size: 20px;
        font-weight: bold;
    }}
    
    .inspirational {{
        text-align: center;
        margin: 60px 0;
        padding: 40px 20px;
        background: #fed7d7;
        color: #c53030;
        font-style: italic;
        font-size: 20px;
        font-weight: 600;
    }}
    
    .footer-text {{
        text-align: center;
        margin: 40px 0;
        padding: 25px;
        background: #667eea;
        color: white;
        font-weight: 600;
        font-size: 18px;
    }}
    
    .signature {{
        text-align: center;
        margin: 20px 0;
        padding: 20px;
        background: #38a169;
        color: white;
        font-weight: 600;
        font-size: 16px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    @media (max-width: 768px) {{
        body {{ padding: 20px 15px; }}
        .header {{ padding: 40px 20px; }}
        .header h1 {{ font-size: 32px; }}
        .question-section {{ padding: 25px 0; }}
        .question-header {{ 
            flex-direction: column; 
            align-items: flex-start;
            gap: 15px;
        }}
        .options-container {{ 
            grid-template-columns: 1fr; 
            gap: 15px; 
        }}
        .option {{ padding: 18px; }}
        .inspirational {{ 
            margin: 40px 0; 
            padding: 30px 20px; 
            font-size: 18px; 
        }}
    }}
</style>
</head>
<body>
<div class='container'>
    <div class='header'>
        <h1>{test_title}</h1>
    </div>
    
    <div class='inspirational'>
        "The only impossible journey is the one you never begin"
    </div>
"""
    
    for idx, q in enumerate(data, 1):
        processed_body = q.get('body') or ""
        if not processed_body and q.get("image"):
            processed_body = f"<img src='{q['image']}' style='max-width:100%; height:auto; margin: 15px 0;'>"

        html += f"""
<div class='question-section'>
    <div class='question-header'>
        <div class='question-number'>Question {idx}</div>
        <div class='watermark'>
            <a href='https://t.me/Harshleaks' target='_blank'>@Harsh</a>
        </div>
    </div>
    <div class='question-text'>{processed_body}</div>
    <div class='options-container'>"""
        
        alternatives = q.get("alternatives", [])[:4]
        labels = ["A", "B", "C", "D"]
        
        for opt_idx, opt in enumerate(alternatives):
            is_correct = str(opt.get("score_if_chosen")) == "1"
            class_name = "option correct" if is_correct else "option"

            processed_answer = opt.get("answer") or ""
            if not processed_answer and opt.get("image"):
                processed_answer = f"<img src='{opt['image']}' style='max-width:100%; height:auto;'>"

            html += f"<div class='{class_name}'><strong>{labels[opt_idx]})</strong> {processed_answer}</div>"
        
        html += "</div></div>"
    
    html += """
    <div class='footer-text'>Knowledge is power, apply it wisely</div>
    <div class='signature'>Generated by Harsh</div>
</div>
</body>
</html>"""
    return html


def generate_html_only_questions(data, test_title, syllabus):
    """Generate HTML with only questions (no answer highlighting) - Modern Premium theme"""
    return generate_html_with_answers(data, test_title, syllabus).replace(
        "class='option correct'", "class='option'"
    ).replace(
        "background: linear-gradient(135deg, #10b981 0%, #059669 100%);",
        "background: linear-gradient(135deg, rgba(51, 65, 85, 0.6) 0%, rgba(30, 41, 59, 0.6) 100%);"
    ).replace(
        "border-color: #34d399;",
        "border: 1px solid rgba(148, 163, 184, 0.2);"
    ).replace(
        "box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4), 0 0 0 1px rgba(52, 211, 153, 0.2);",
        ""
    ).replace(
        ".option.correct::before {",
        ".option.correct-hidden::before {"
    )

def generate_answer_key_table(data, test_title, syllabus):
    """Generate HTML answer key table - Modern Premium theme (with MathJax & image support)"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<title>{test_title} - Answer Key</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    
    body {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: radial-gradient(circle at 80% 20%, #1e3a8a 0%, #000000 50%, #312e81 100%);
        background-attachment: fixed;
        color: #f8fafc;
        padding: 24px;
        margin: 0;
        min-height: 100vh;
        position: relative;
    }}
    
    body::before {{
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: url('data:image/svg+xml,<svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd"><circle fill="%23ffffff" fill-opacity="0.03" cx="20" cy="20" r="1"/></g></svg>');
        z-index: -1;
        opacity: 0.6;
    }}
    
    .title-box {{
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        backdrop-filter: blur(20px);
        padding: 32px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 32px;
        box-shadow: 0 20px 40px rgba(59, 130, 246, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        position: relative;
        overflow: hidden;
    }}
    
    .title-box::before {{
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        animation: shine 3s infinite;
    }}
    
    @keyframes shine {{
        0% {{ transform: translateX(-100%) translateY(-100%); }}
        100% {{ transform: translateX(100%) translateY(100%); }}
    }}
    
    .title-box h1 {{
        position: relative;
        z-index: 1;
        font-size: 28px;
        font-weight: 700;
        background: linear-gradient(135deg, #ffffff 0%, #dbeafe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 8px 0;
    }}
    
    .title-box div {{
        position: relative;
        z-index: 1;
        font-size: 16px;
        color: #bfdbfe;
        font-weight: 500;
    }}
    
    .answer-key-container {{
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(148, 163, 184, 0.2);
    }}
    
    .answer-key-table {{
        width: 100%;
        border-collapse: collapse;
    }}
    
    .answer-key-table th {{
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.3) 0%, rgba(29, 78, 216, 0.3) 100%);
        color: #dbeafe;
        padding: 18px 16px;
        text-align: center;
        font-weight: 600;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border-bottom: 2px solid rgba(59, 130, 246, 0.5);
    }}
    
    .answer-key-table td {{
        padding: 16px;
        text-align: center;
        border-bottom: 1px solid rgba(148, 163, 184, 0.1);
        color: #cbd5e1;
        font-weight: 400;
        vertical-align: middle;
    }}
    
    .answer-key-table tr:nth-child(even) {{
        background: rgba(255, 255, 255, 0.02);
    }}
    
    .answer-key-table tr:hover {{
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(29, 78, 216, 0.1) 100%);
        transform: scale(1.001);
        transition: all 0.3s ease;
    }}
    
    .question-number {{
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: #ffffff;
        padding: 8px 14px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 13px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 40px;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }}
    
    .correct-option {{
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: #ffffff;
        padding: 8px 14px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 13px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 40px;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
        position: relative;
    }}
    
    .correct-option::before {{
        content: '✓';
        margin-right: 4px;
        font-size: 12px;
    }}
    
    .answer-text {{
        text-align: left;
        color: #e2e8f0;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(79, 70, 229, 0.1) 100%);
        backdrop-filter: blur(10px);
        padding: 12px 16px;
        border-radius: 12px;
        border-left: 3px solid #6366f1;
        font-weight: 400;
        line-height: 1.5;
        max-width: 400px;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.1);
    }}
    
    .quote {{
        text-align: center;
        margin: 32px auto;
        padding: 24px 32px;
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%);
        backdrop-filter: blur(20px);
        color: #fbbf24;
        border-radius: 16px;
        font-style: italic;
        font-size: 18px;
        font-weight: 500;
        box-shadow: 0 10px 30px rgba(245, 158, 11, 0.2), 0 0 0 1px rgba(245, 158, 11, 0.2);
        border: 1px solid rgba(245, 158, 11, 0.3);
        max-width: 600px;
        position: relative;
    }}
    
    .quote-footer, .extracted-box {{
        text-align: center;
        margin: 24px auto;
        padding: 16px 24px;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(29, 78, 216, 0.2) 100%);
        backdrop-filter: blur(20px);
        color: #93c5fd;
        border-radius: 12px;
        font-weight: 600;
        font-size: 14px;
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.2), 0 0 0 1px rgba(59, 130, 246, 0.2);
        border: 1px solid rgba(59, 130, 246, 0.3);
        max-width: fit-content;
    }}
    
    .extracted-box {{
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.2) 0%, rgba(126, 34, 206, 0.2) 100%);
        color: #d8b4fe;
        border-color: rgba(168, 85, 247, 0.3);
        box-shadow: 0 8px 20px rgba(168, 85, 247, 0.2), 0 0 0 1px rgba(168, 85, 247, 0.2);
    }}
    
    @media print {{
        body {{ 
            background: #000 !important; 
            -webkit-print-color-adjust: exact;
        }}
        .answer-key-container {{ 
            background: #1e293b !important;
        }}
    }}
    
    @media (max-width: 768px) {{
        body {{ padding: 16px; }}
        .title-box {{ padding: 24px 20px; }}
        .title-box h1 {{ font-size: 24px; }}
        .answer-key-table th, .answer-key-table td {{ padding: 12px 8px; font-size: 13px; }}
        .answer-text {{ max-width: 100%; }}
    }}
</style>
<!-- MathJax for equations -->
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</head>
<body>
<div class='title-box'>
    <h1>{test_title}</h1>
    <div>🎯Answer Key & Solutions</div>
</div>
<div class='quote'>"𝑻𝒉𝒆 𝒐𝒏𝒍𝒚 𝒊𝒎𝒑𝒐𝒔𝒔𝒊𝒃𝒍𝒆 𝒋𝒐𝒖𝒓𝒏𝒆𝒚 𝒊𝒔 𝒕𝒉𝒆 𝒐𝒏𝒆 𝒚𝒐𝒖 𝒏𝒆𝒗𝒆𝒓 𝒃𝒆𝒈𝒊𝒏" </div>

<div class='answer-key-container'>
<table class='answer-key-table'>
    <thead>
        <tr>
            <th>Question No.</th>
            <th>Correct Option</th>
            <th>Answer Text</th>
        </tr>
    </thead>
    <tbody>"""
    
    for idx, q in enumerate(data, 1):
        correct_option = ""
        correct_answer = ""
        
        for i, opt in enumerate(q["alternatives"][:4]):
            if str(opt.get("score_if_chosen")) == "1":
                correct_option = ["A", "B", "C", "D"][i]
                # handle both text and image
                correct_answer = process_html_content(opt.get('answer')) or ""
                if not correct_answer and opt.get("image"):
                    correct_answer = f"<img src='{opt['image']}' style='max-width:100%; height:auto;'>"
                break
        
        html += f"""
        <tr>
            <td><span class='question-number'>{idx}</span></td>
            <td><span class='correct-option'>{correct_option}</span></td>
            <td><div class='answer-text'>{correct_answer}</div></td>
        </tr>"""
    
    html += """
    </tbody>
</table>
</div>
<div class='quote-footer'>"𝕂𝕟𝕠𝕨𝕝𝕖𝕕𝕘𝕖 𝕚𝕤 𝕡𝕠𝕨𝕖𝕣, 𝕒𝕡𝕡𝕝𝕪 𝕚𝕥 𝕨𝕚𝕤𝕖𝕝𝕪"</div>
<div class='extracted-box'>"𝒢𝐸𝒩𝐸𝑅𝒜𝒯𝐸𝒟 𝐵𝒴 𝐻𝒜𝑅𝒮𝐻"</div>
</body>
</html>"""
    return html

# === Main ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("extract", extract_command)],
        states={ASK_NID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_nid)]},
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("au", authorize_user))
    app.add_handler(CommandHandler("ru", revoke_user))
    app.add_handler(CommandHandler("send", send_command))

    app.add_handler(conv_handler)

    logger.info("Bot started...")
    app.run_polling()



if __name__ == '__main__':
    main()
