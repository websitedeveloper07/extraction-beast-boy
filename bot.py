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
import re
from html import unescape
from datetime import datetime, timezone, timedelta

# === CONFIG ===
BOT_TOKEN = "8281535597:AAH8cE1IHd8gciFTLkqx_fizHsV0fuK6A1Q"
OWNER_IDS = {8516723793}  # Bot owners
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
    """Extract syllabus information from the description HTML"""
    if not description:
        return {}
    
    # Decode HTML entities
    decoded_description = unescape(description)
    
    soup = BeautifulSoup(decoded_description, 'html.parser')
    syllabus = {}
    
    # Find all strong tags and extract the subject and content
    for strong_tag in soup.find_all('strong'):
        subject_text = strong_tag.get_text().strip()
        if ':' in subject_text:
            subject = subject_text.split(':')[0].strip()
            # Get the content after the strong tag until the next <br> or end
            content = ""
            next_sibling = strong_tag.next_sibling
            while next_sibling and next_sibling.name != 'br':
                if hasattr(next_sibling, 'get_text'):
                    content += next_sibling.get_text()
                elif isinstance(next_sibling, str):
                    content += next_sibling
                next_sibling = next_sibling.next_sibling
            
            syllabus[subject] = content.strip()
    
    return syllabus

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
            title = data[0].get("title", f"Test_{nid}")
            description = data[0].get("description", "")
            syllabus = extract_syllabus(description)
            return title, description, syllabus
    except:
        pass
    return f"Test_{nid}", "", {}

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

    # Fetch test title, description, and syllabus
    title, desc, syllabus = fetch_test_title_and_description(nid)

    # Generate HTML files
    htmls = {
        "QP_with_Answers.html": generate_html_with_answers(data, title, desc, syllabus),
        "Only_Answer_Key.html": generate_answer_key_table(data, title, desc, syllabus),
        "Only_Question_Paper.html": generate_html_only_questions(data, title, desc, syllabus)
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

# === HTML Generators - New Clean Layout ===
def generate_html_with_answers(data, test_title, description, syllabus):
    """Generate HTML with questions and highlighted correct answers - Clean Modern Layout"""
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<title>{test_title}</title>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    
    body {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: #f8f9fa;
        color: #212529;
        line-height: 1.6;
        padding: 20px;
    }}
    
    .paper {{
        max-width: 900px;
        margin: 0 auto;
        background: white;
        box-shadow: 0 0 20px rgba(0,0,0,0.1);
        border-radius: 8px;
        overflow: hidden;
    }}
    
    .header {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        text-align: center;
        position: relative;
    }}
    
    .header h1 {{
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }}
    
    .header p {{
        font-size: 16px;
        opacity: 0.9;
    }}
    
    .syllabus {{
        background: #e8f4fd;
        padding: 25px;
        border-bottom: 2px solid #bee5eb;
    }}
    
    .syllabus h2 {{
        color: #0c5460;
        font-size: 20px;
        margin-bottom: 15px;
        text-align: center;
    }}
    
    .syllabus-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 15px;
    }}
    
    .syllabus-item {{
        background: white;
        padding: 15px;
        border-radius: 6px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border-left: 4px solid #17a2b8;
    }}
    
    .syllabus-item h3 {{
        color: #0c5460;
        font-size: 16px;
        margin-bottom: 8px;
    }}
    
    .syllabus-item p {{
        color: #495057;
        font-size: 14px;
        margin: 0;
    }}
    
    .content {{
        padding: 30px;
    }}
    
    .question {{
        margin-bottom: 30px;
        padding: 20px;
        background: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        position: relative;
    }}
    
    .question-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid #dee2e6;
    }}
    
    .question-number {{
        background: #007bff;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
    }}
    
    .watermark {{
        background: #dc3545;
        color: white;
        padding: 5px 12px;
        border-radius: 15px;
        font-size: 12px;
        font-weight: bold;
    }}
    
    .watermark a {{
        color: white;
        text-decoration: none;
    }}
    
    .question-text {{
        font-size: 16px;
        margin-bottom: 20px;
        color: #212529;
        font-weight: 500;
    }}
    
    .options {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
    }}
    
    .option {{
        padding: 15px;
        background: white;
        border: 2px solid #dee2e6;
        border-radius: 6px;
        font-size: 15px;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
    }}
    
    .option:hover {{
        border-color: #007bff;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,123,255,0.2);
    }}
    
    .option.correct {{
        background: #28a745;
        color: white;
        border-color: #28a745;
        font-weight: 600;
    }}
    
    .option.correct::after {{
        content: '✓';
        margin-left: 10px;
        font-weight: bold;
        font-size: 18px;
    }}
    
    .option-label {{
        font-weight: bold;
        margin-right: 10px;
        color: #007bff;
        min-width: 25px;
    }}
    
    .option.correct .option-label {{
        color: white;
    }}
    
    .footer {{
        background: #343a40;
        color: white;
        text-align: center;
        padding: 25px;
    }}
    
    .footer p {{
        font-size: 16px;
        margin-bottom: 10px;
    }}
    
    .footer .signature {{
        font-size: 14px;
        opacity: 0.8;
    }}
    
    img {{
        max-width: 100%;
        height: auto;
        border-radius: 6px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    
    @media print {{
        body {{ background: white; }}
        .paper {{ box-shadow: none; }}
        .question {{ page-break-inside: avoid; }}
        .syllabus {{ page-break-after: always; }}
    }}
    
    @media (max-width: 768px) {{
        .options {{ grid-template-columns: 1fr; }}
        .header h1 {{ font-size: 24px; }}
        .content {{ padding: 20px; }}
    }}
</style>
</head>
<body>
<div class='paper'>
    <div class='header'>
        <h1>{test_title}</h1>
        <p>Question Paper with Answers</p>
    </div>
    
    <div class='syllabus'>
        <h2>📚 Syllabus</h2>
        <div class='syllabus-grid'>"""
    
    # Add syllabus items
    if syllabus:
        for subject, content in syllabus.items():
            html += f"""
            <div class='syllabus-item'>
                <h3>{subject}</h3>
                <p>{content}</p>
            </div>"""
    else:
        html += """
            <div class='syllabus-item'>
                <p>Syllabus information not available</p>
            </div>"""
    
    html += """
        </div>
    </div>
    
    <div class='content'>"""
    
    for idx, q in enumerate(data, 1):
        question_body = q.get('body', '').replace('src="//', 'src="https://')
        
        html += f"""
        <div class='question'>
            <div class='question-header'>
                <span class='question-number'>Question {idx}</span>
                <span class='watermark'><a href='https://t.me/+cKL6ndt3C7IzMGE1' target='_blank'>@Harsh</a></span>
            </div>
            <div class='question-text'>{question_body}</div>
            <div class='options'>"""
        
        alternatives = q.get("alternatives", [])[:4]
        labels = ["A", "B", "C", "D"]
        
        for opt_idx, opt in enumerate(alternatives):
            is_correct = str(opt.get("score_if_chosen")) == "1"
            class_name = "option correct" if is_correct else "option"
            
            option_body = opt.get("answer", "").replace('src="//', 'src="https://')
            
            html += f"""
                <div class='{class_name}'>
                    <span class='option-label'>{labels[opt_idx]}.</span>
                    <span>{option_body}</span>
                </div>"""
        
        html += """
            </div>
        </div>"""
    
    html += """
    </div>
    
    <div class='footer'>
        <p>"Fall seven times, stand up eight."</p>
        <div class='signature'>Generated by Harsh</div>
    </div>
</div>
</body>
</html>"""
    return html

def generate_html_only_questions(data, test_title, description, syllabus):
    """Generate HTML with only questions (no answer highlighting)"""
    return generate_html_with_answers(data, test_title, description, syllabus).replace(
        "class='option correct'", "class='option'"
    ).replace(
        ".option.correct::after { content: '✓'; margin-left: 10px; font-weight: bold; font-size: 18px; }",
        ""
    )

def generate_answer_key_table(data, test_title, description, syllabus):
    """Generate HTML answer key table"""
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<title>{test_title} - Answer Key</title>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    
    body {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: #f8f9fa;
        color: #212529;
        line-height: 1.6;
        padding: 20px;
    }}
    
    .paper {{
        max-width: 900px;
        margin: 0 auto;
        background: white;
        box-shadow: 0 0 20px rgba(0,0,0,0.1);
        border-radius: 8px;
        overflow: hidden;
    }}
    
    .header {{
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        padding: 30px;
        text-align: center;
    }}
    
    .header h1 {{
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }}
    
    .header p {{
        font-size: 16px;
        opacity: 0.9;
    }}
    
    .syllabus {{
        background: #e8f5e8;
        padding: 25px;
        border-bottom: 2px solid #c3e6cb;
    }}
    
    .syllabus h2 {{
        color: #155724;
        font-size: 20px;
        margin-bottom: 15px;
        text-align: center;
    }}
    
    .syllabus-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 15px;
    }}
    
    .syllabus-item {{
        background: white;
        padding: 15px;
        border-radius: 6px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border-left: 4px solid #28a745;
    }}
    
    .syllabus-item h3 {{
        color: #155724;
        font-size: 16px;
        margin-bottom: 8px;
    }}
    
    .syllabus-item p {{
        color: #495057;
        font-size: 14px;
        margin: 0;
    }}
    
    .content {{
        padding: 30px;
    }}
    
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }}
    
    th {{
        background: #28a745;
        color: white;
        padding: 15px;
        text-align: left;
        font-weight: 600;
        font-size: 16px;
    }}
    
    td {{
        padding: 12px 15px;
        border-bottom: 1px solid #dee2e6;
        font-size: 15px;
    }}
    
    tr:nth-child(even) {{
        background: #f8f9fa;
    }}
    
    tr:hover {{
        background: #e8f5e8;
    }}
    
    .q-number {{
        background: #007bff;
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-weight: bold;
        display: inline-block;
    }}
    
    .correct-option {{
        background: #ffc107;
        color: #212529;
        padding: 5px 10px;
        border-radius: 15px;
        font-weight: bold;
        display: inline-block;
    }}
    
    .answer-text {{
        font-style: italic;
        color: #495057;
    }}
    
    .footer {{
        background: #343a40;
        color: white;
        text-align: center;
        padding: 25px;
    }}
    
    .footer p {{
        font-size: 16px;
        margin-bottom: 10px;
    }}
    
    .footer .signature {{
        font-size: 14px;
        opacity: 0.8;
    }}
    
    @media print {{
        body {{ background: white; }}
        .paper {{ box-shadow: none; }}
        thead {{ display: table-header-group; }}
    }}
    
    @media (max-width: 768px) {{
        .content {{ padding: 20px; }}
        th, td {{ padding: 10px; font-size: 14px; }}
    }}
</style>
</head>
<body>
<div class='paper'>
    <div class='header'>
        <h1>{test_title}</h1>
        <p>Answer Key</p>
    </div>
    
    <div class='syllabus'>
        <h2>📚 Syllabus</h2>
        <div class='syllabus-grid'>"""
    
    # Add syllabus items
    if syllabus:
        for subject, content in syllabus.items():
            html += f"""
            <div class='syllabus-item'>
                <h3>{subject}</h3>
                <p>{content}</p>
            </div>"""
    else:
        html += """
            <div class='syllabus-item'>
                <p>Syllabus information not available</p>
            </div>"""
    
    html += """
        </div>
    </div>
    
    <div class='content'>
        <table>
            <thead>
                <tr>
                    <th>Question No.</th>
                    <th>Correct Option</th>
                    <th>Answer</th>
                </tr>
            </thead>
            <tbody>"""
    
    for idx, q in enumerate(data, 1):
        correct_option = ""
        correct_answer = "No answer"
        
        for i, opt in enumerate(q.get("alternatives", [])[:4]):
            if str(opt.get("score_if_chosen")) == "1":
                correct_option = ["A", "B", "C", "D"][i]
                answer_content = opt.get("answer", "").replace('src="//', 'src="https://')
                correct_answer = answer_content if answer_content else "No answer"
                break
        
        html += f"""
                <tr>
                    <td><span class='q-number'>{idx}</span></td>
                    <td><span class='correct-option'>{correct_option}</span></td>
                    <td class='answer-text'>{correct_answer}</td>
                </tr>"""
    
    html += """
            </tbody>
        </table>
    </div>
    
    <div class='footer'>
        <p>"Fall seven times, stand up eight."</p>
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


if __name__ == "__main__":
    main()
