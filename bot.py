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
    """Generate HTML with questions and highlighted correct answers - Enhanced Vibrant Layout with Image Support"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<title>{test_title}</title>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@500;600;700&display=swap');
    
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    
    body {{
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        color: #2d3748;
        padding: 25px;
        line-height: 1.6;
        min-height: 100vh;
    }}

    .container {{
        max-width: 1000px;
        margin: 0 auto;
        background: white;
        border-radius: 16px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        overflow: hidden;
    }}

    .header {{
        text-align: center;
        padding: 25px 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        position: relative;
    }}

    .header::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="20" cy="20" r="2" fill="rgba(255,255,255,0.1)"/><circle cx="80" cy="40" r="1.5" fill="rgba(255,255,255,0.1)"/><circle cx="40" cy="80" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="90" cy="90" r="2" fill="rgba(255,255,255,0.1)"/></svg>');
    }}
    
    .header h1 {{
        font-family: 'Poppins', sans-serif;
        font-size: 28px;
        font-weight: 700;
        margin: 0;
        position: relative;
        z-index: 1;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }}

    .header-subtitle {{
        font-size: 14px;
        margin-top: 6px;
        opacity: 0.9;
        position: relative;
        z-index: 1;
    }}

    .quote-section {{
        padding: 18px 25px;
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        text-align: center;
        border-bottom: 3px solid #ff8a65;
    }}

    .quote-text {{
        font-family: 'Poppins', sans-serif;
        font-size: 16px;
        font-weight: 600;
        color: #d84315;
        font-style: italic;
        position: relative;
    }}

    .quote-text::before {{
        content: '"';
        font-size: 28px;
        position: absolute;
        left: -15px;
        top: -6px;
        opacity: 0.6;
    }}

    .quote-text::after {{
        content: '"';
        font-size: 28px;
        position: absolute;
        right: -15px;
        bottom: -12px;
        opacity: 0.6;
    }}
    
    .question-container {{
        padding: 20px;
    }}

    /* PDF Print Styles */
    @media print {{
        body {{
            background: white;
            padding: 10px;
        }}
        
        .container {{
            box-shadow: none;
            border-radius: 0;
        }}
        
        .question-box {{
            page-break-inside: avoid;
            break-inside: avoid;
            margin-bottom: 15px;
            box-shadow: none;
            border: 1px solid #e2e8f0;
        }}
        
        .question-box:hover {{
            transform: none;
            box-shadow: none;
        }}
        
        .option:hover {{
            transform: none;
            box-shadow: none;
        }}
        
        .header {{
            page-break-after: avoid;
        }}
        
        .quote-section {{
            page-break-after: avoid;
            margin-bottom: 20px;
        }}
        
        /* Ensure question and options stay together */
        .question-content {{
            page-break-inside: avoid;
            break-inside: avoid;
        }}
        
        .options-grid {{
            page-break-inside: avoid;
            break-inside: avoid;
        }}
    }}

    .question-box {{
        background: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 8px;
        margin-bottom: 20px;
        overflow: hidden;
        transition: all 0.3s ease;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
        page-break-inside: avoid;
        break-inside: avoid;
    }}

    .question-box:hover {{
        border-color: #667eea;
        box-shadow: 0 6px 18px rgba(102, 126, 234, 0.12);
        transform: translateY(-1px);
    }}
    
    .question-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 18px;
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-bottom: 1px solid #cbd5e0;
    }}
    
    .question-number {{
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        padding: 6px 14px;
        font-size: 14px;
        font-weight: 700;
        border-radius: 15px;
        box-shadow: 0 3px 8px rgba(66, 153, 225, 0.25);
    }}
    
    .watermark {{
        background: linear-gradient(135deg, #fc8181 0%, #e53e3e 100%);
        color: white;
        padding: 5px 12px;
        font-size: 11px;
        font-weight: 600;
        border-radius: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 6px rgba(252, 129, 129, 0.25);
    }}
    
    .watermark a {{
        color: white;
        text-decoration: none;
    }}
    
    .question-content {{
        padding: 18px;
    }}
    
    .question-text {{
        font-size: 16px;
        margin-bottom: 18px;
        color: #2d3748;
        font-weight: 500;
        line-height: 1.6;
    }}

    .question-image {{
        max-width: 100%;
        height: auto;
        border-radius: 8px;
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        display: block;
    }}
    
    .options-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
    }}
    
    .option {{
        padding: 12px 15px;
        font-size: 14px;
        color: #4a5568;
        border: 2px solid #cbd5e0;
        background: linear-gradient(135deg, #ffffff 0%, #f7fafc 100%);
        border-radius: 6px;
        transition: all 0.2s ease;
        font-weight: 500;
        cursor: pointer;
        position: relative;
        min-height: 45px;
        display: flex;
        align-items: center;
    }}
    
    .option:hover {{
        border-color: #667eea;
        background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
    }}
    
    .option.correct {{
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        border-color: #38a169;
        color: white;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(72, 187, 120, 0.25);
    }}
    
    .option.correct::after {{
        content: '✓';
        position: absolute;
        top: 8px;
        right: 12px;
        font-size: 16px;
        font-weight: bold;
        background: rgba(255, 255, 255, 0.2);
        width: 22px;
        height: 22px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
    }}

    .option-label {{
        font-weight: 700;
        margin-right: 8px;
        font-size: 14px;
        color: #667eea;
        flex-shrink: 0;
    }}

    .option.correct .option-label {{
        color: rgba(255, 255, 255, 0.9);
    }}

    .option-image {{
        max-width: 100%;
        height: auto;
        border-radius: 6px;
        margin: 8px 0;
        display: block;
    }}
    
    .footer-section {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        padding: 30px;
    }}
    
    .footer-text {{
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 15px;
        font-family: 'Poppins', sans-serif;
    }}
    
    .signature {{
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        opacity: 0.9;
        background: rgba(255, 255, 255, 0.1);
        padding: 8px 16px;
        border-radius: 20px;
        display: inline-block;
    }}

    /* Enhanced Image Support */
    img {{
        max-width: 100%;
        height: auto;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        margin: 10px 0;
        display: block;
    }}

    .image-placeholder {{
        background: #f7fafc;
        border: 2px dashed #cbd5e0;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        color: #a0aec0;
        font-style: italic;
        margin: 10px 0;
    }}
    
    @media (max-width: 768px) {{
        body {{ padding: 15px; }}
        .header {{ padding: 30px 20px; }}
        .header h1 {{ font-size: 28px; }}
        .question-container {{ padding: 20px; }}
        .question-header {{ 
            flex-direction: column; 
            gap: 12px;
            text-align: center;
        }}
        .options-grid {{ 
            grid-template-columns: 1fr; 
            gap: 12px;
        }}
        .option {{ 
            padding: 16px 18px; 
            font-size: 15px;
            min-height: 50px;
        }}
        .quote-section {{ padding: 20px; }}
        .quote-text {{ font-size: 18px; }}
    }}
</style>
</head>
<body>
<div class='container'>
    <div class='header'>
        <h1>{test_title}</h1>
        <div class='header-subtitle'>Master Your Knowledge</div>
    </div>
    
    <div class='quote-section'>
        <div class='quote-text'>The only impossible journey is the one you never begin</div>
    </div>

    <div class='question-container'>
"""
    
    for idx, q in enumerate(data, 1):
        processed_body = q.get('body') or ""
        
        # Enhanced image handling
        if not processed_body and q.get("image"):
            image_url = q['image']
            processed_body = f"<img src='{image_url}' alt='Question {idx} Image' class='question-image' onerror=\"this.style.display='none'; this.nextElementSibling.style.display='block';\" /><div class='image-placeholder' style='display:none;'>Image not available</div>"
        elif q.get("image"):
            image_url = q['image']
            processed_body += f"<br><img src='{image_url}' alt='Question {idx} Image' class='question-image' onerror=\"this.style.display='none'; this.nextElementSibling.style.display='block';\" /><div class='image-placeholder' style='display:none;'>Image not available</div>"

        html += f"""
        <div class='question-box'>
            <div class='question-header'>
                <div class='question-number'>Question {idx}</div>
                <div class='watermark'>
                    <a href='https://t.me/Harshleaks' target='_blank'>@Harsh</a>
                </div>
            </div>
            <div class='question-content'>
                <div class='question-text'>{processed_body}</div>
                <div class='options-grid'>"""
        
        alternatives = q.get("alternatives", [])[:4]
        labels = ["A", "B", "C", "D"]
        
        for opt_idx, opt in enumerate(alternatives):
            is_correct = str(opt.get("score_if_chosen")) == "1"
            class_name = "option correct" if is_correct else "option"

            processed_answer = opt.get("answer") or ""
            
            # Enhanced image handling for options
            if not processed_answer and opt.get("image"):
                image_url = opt['image']
                processed_answer = f"<img src='{image_url}' alt='Option {labels[opt_idx]}' class='option-image' onerror=\"this.style.display='none'; this.nextElementSibling.style.display='block';\" /><div class='image-placeholder' style='display:none;'>Image not available</div>"
            elif opt.get("image"):
                image_url = opt['image']
                processed_answer += f"<br><img src='{image_url}' alt='Option {labels[opt_idx]}' class='option-image' onerror=\"this.style.display='none'; this.nextElementSibling.style.display='block';\" /><div class='image-placeholder' style='display:none;'>Image not available</div>"

            html += f"""
                <div class='{class_name}'>
                    <span class='option-label'>{labels[opt_idx]})</span>
                    <div>{processed_answer}</div>
                </div>"""
        
        html += """
                </div>
            </div>
        </div>"""
    
    html += """
    </div>
    
    <div class='footer-section'>
        <div class='footer-text'>Knowledge is power, apply it wisely</div>
        <div class='signature'>Generated by Harsh</div>
    </div>
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
    """Generate HTML answer key table with watermark and repeating headers"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<title>{test_title} - Answer Key</title>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@500;600;700&display=swap');
    
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    
    body {{
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        color: #2d3748;
        padding: 25px;
        line-height: 1.6;
        min-height: 100vh;
        position: relative;
    }}

    /* 🔹 Watermark for screen */
    body::before {{
      content: '';
      position: fixed;
      top: 50%;
      left: 50%;
      width: 300px;      /* smaller size */
      height: 300px;
      background: url('https://i.postimg.cc/DwqS1pxt/image-removebg-preview-1.png') no-repeat center;
      background-size: contain;
      opacity: 0.2;      /* lighter transparency */
      transform: translate(-50%, -50%) rotate(-30deg);
      z-index: -1;
      pointer-events: none;
    }}

    /* 🔹 Watermark for PDF/print */
    @media print {{
      body::before {{
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 300px;    /* same small size */
        height: 300px;
        background: url('https://i.postimg.cc/DwqS1pxt/image-removebg-preview-1.png') no-repeat center;
        background-size: contain;
        opacity: 0.2;
        transform: translate(-50%, -50%) rotate(-30deg);
        z-index: -1;
      }}

      body {{
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }}
    }}
    
    .container {{
        max-width: 1200px;
        margin: 0 auto;
        background: white;
        border-radius: 16px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        position: relative;
        z-index: 1;
    }}

    .header {{
        text-align: center;
        padding: 25px 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        position: relative;
    }}

    .header h1 {{
        font-family: 'Poppins', sans-serif;
        font-size: 28px;
        font-weight: 700;
        margin: 0;
        z-index: 1;
    }}

    .header-subtitle {{
        font-size: 14px;
        margin-top: 6px;
        opacity: 0.9;
    }}

    .quote-section {{
        padding: 18px 25px;
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        text-align: center;
        border-bottom: 3px solid #ff8a65;
    }}

    .quote-text {{
        font-family: 'Poppins', sans-serif;
        font-size: 16px;
        font-weight: 600;
        color: #d84315;
        font-style: italic;
    }}

    .answer-key-container {{
        padding: 20px;
    }}

    /* ✅ Use real table so headers repeat on page breaks */
    table.answer-key-table {{
        width: 100%;
        border-collapse: collapse;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }}

    thead {{
        display: table-header-group; /* repeat headers on new page */
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
    }}

    thead th {{
        padding: 14px;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-right: 1px solid rgba(255, 255, 255, 0.2);
        text-align: center;
    }}

    thead th:last-child {{
        border-right: none;
    }}

    tbody td {{
        border-bottom: 1px solid #e2e8f0;
        padding: 12px;
        font-size: 14px;
        background: #ffffff;
        text-align: center;
    }}

    tbody tr:nth-child(even) td {{
        background: #f8fafc;
    }}

    .question-number {{
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        padding: 6px 12px;
        border-radius: 12px;
        font-weight: 700;
    }}

    .correct-option {{
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        padding: 6px 12px;
        border-radius: 12px;
        font-weight: 700;
    }}

    .answer-text {{
        color: #2d3748;
        font-weight: 500;
        line-height: 1.6;
        padding: 8px 12px;
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        border-radius: 8px;
        border-left: 3px solid #667eea;
        text-align: left;
    }}

    .answer-image {{
        max-width: 200px;
        max-height: 100px;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        margin: 5px 0;
    }}

    .image-placeholder {{
        background: #f7fafc;
        border: 2px dashed #cbd5e0;
        border-radius: 6px;
        padding: 10px;
        text-align: center;
        color: #a0aec0;
        font-size: 12px;
        margin: 5px 0;
    }}

    .footer-section {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        padding: 30px;
    }}

    .footer-text {{
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 15px;
        font-family: 'Poppins', sans-serif;
    }}

    .signature {{
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        opacity: 0.9;
        background: rgba(255, 255, 255, 0.1);
        padding: 8px 16px;
        border-radius: 20px;
        display: inline-block;
    }}
</style>
</head>
<body>
<div class='container'>
    <div class='header'>
        <h1>{test_title}</h1>
        <div class='header-subtitle'>Answer Key</div>
    </div>
    
    <div class='quote-section'>
        <div class='quote-text'>The only impossible journey is the one you never begin</div>
    </div>

    <div class='answer-key-container'>
        <table class='answer-key-table'>
            <thead>
                <tr>
                    <th>Question No.</th>
                    <th>Correct Option</th>
                    <th>Answer Text</th>
                </tr>
            </thead>
            <tbody>
"""
    # loop for rows
    for idx, q in enumerate(data, 1):
        correct_option = ""
        correct_answer = "<em>No answer</em>"
        
        for i, opt in enumerate(q.get("alternatives", [])[:4]):
            if str(opt.get("score_if_chosen")) == "1":
                correct_option = ["A", "B", "C", "D"][i]
                answer_text = opt.get("answer", "").strip()
                answer_image = opt.get("image", "").strip()
                if answer_text and answer_image:
                    correct_answer = f"""{answer_text}<br>
                    <img src='{answer_image}' class='answer-image' 
                         alt='Answer {correct_option}' 
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='block';"/>
                    <div class='image-placeholder' style='display:none;'>Image not available</div>"""
                elif answer_image:
                    correct_answer = f"""<img src='{answer_image}' class='answer-image' 
                         alt='Answer {correct_option}' 
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='block';"/>
                    <div class='image-placeholder' style='display:none;'>Image not available</div>"""
                elif answer_text:
                    correct_answer = answer_text
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
    
    <div class='footer-section'>
        <div class='footer-text'>Knowledge is power, apply it wisely</div>
        <div class='signature'>Generated by Harsh</div>
    </div>
</div>
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
