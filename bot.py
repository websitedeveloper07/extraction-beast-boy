import os
import json
import logging
import requests
from io import BytesIO
from bs4 import BeautifulSoup
import psutil
from telegram import InputMediaDocument

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# === CONFIG ===
BOT_TOKEN = "8163450084:AAFCadeMAzxD6Rb6nfYwJ5Ke5IR8HcCIhWM"  # Replace with your token
OWNER_ID = 7796598050
AUTHORIZED_USER_IDS = {OWNER_ID}
PLAN = "PRO PLAN⚡"

ASK_NID = 0
extracted_papers_count = 0
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_authorized(user_id):
    return user_id in AUTHORIZED_USER_IDS

async def send_unauthorized_message(update: Update):
    if update.message:
        await update.message.reply_text("❌ Access Denied. You are not authorized to use this bot.")
    elif update.callback_query:
        await update.callback_query.answer("❌ Access Denied!", show_alert=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await send_unauthorized_message(update)
        return

    await update.message.reply_text(
        """🤖 *Paper Extractor Bot*

Commands:
• `/extract` - Extracts and sends all 3 HTML formats for a given NID.
• `/status` - Shows bot status, usage, and plan.
• `/info <nid>` Gives info about nid, Test title/Display name etc.
• `/au <user_id>` - Authorize a user (owner only).
• `/ru <user_id>` - Revoke a user (owner only). 
""",
        parse_mode='Markdown'
    )

async def authorize_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Only the bot owner can use this command.")
        return

    try:
        user_id = int(context.args[0])
        AUTHORIZED_USER_IDS.add(user_id)
        await update.message.reply_text(f"✅ User ID {user_id} authorized.")
    except:
        await update.message.reply_text("❌ Invalid usage. Example: /au 123456789")

async def revoke_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Only the bot owner can use this command.")
        return

    try:
        user_id = int(context.args[0])
        if user_id == OWNER_ID:
            await update.message.reply_text("🚫 You cannot revoke yourself.")
            return
        AUTHORIZED_USER_IDS.discard(user_id)
        await update.message.reply_text(f"🗑️ User ID {user_id} revoked.")
    except:
        await update.message.reply_text("❌ Invalid usage. Example: /ru 123456789")

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
👑 Owner: *『𝗥ᴏᴄ𝗄𝑦』*
"""
    await update.message.reply_text(msg, parse_mode='Markdown')

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await send_unauthorized_message(update)
        return

    if not context.args:
        await update.message.reply_text("❌ Please provide a NID. Example: /info 4385527980")
        return

    nid = context.args[0]
    try:
        url = f"https://learn.aakashitutor.com/api/getquizfromid?nid={nid}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        print("INFO DEBUG:", json.dumps(data, indent=2))  # log for debug

        # Fix: Handle list or dict formats
        if isinstance(data, list) and len(data) > 0:
            quiz = data[0]
        elif isinstance(data, dict) and "nid" in data:
            quiz = data
        else:
            raise ValueError("Unexpected format or empty response")

        title = quiz.get("title", "N/A")
        display_name = quiz.get("display_name", "N/A")
        syllabus = quiz.get("content_groups_title", "N/A")

        msg = f"""📑 *Test Info*

🆔 *NID:* `{nid}`
📝 *Title:* *{title}*
📛 *Display Name:* *{display_name}*
📚 *Syllabus:* *{syllabus}*
"""
        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        print("INFO ERROR:", e)
        await update.message.reply_text(f"❌ Failed to fetch info for NID `{nid}`.", parse_mode="Markdown")



async def extract_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await send_unauthorized_message(update)
        return ConversationHandler.END

    await update.message.reply_text("🔢 Please send the NID to extract:")
    return ASK_NID

async def handle_nid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global extracted_papers_count
    nid = update.message.text.strip()
    if not nid.isdigit():
        await update.message.reply_text("❌ Invalid NID. Please send numbers only.")
        return ASK_NID

    await update.message.reply_text("🔍 Extracting data and generating HTMLs...")

    data = fetch_locale_json_from_api(nid)
    if not data:
        await update.message.reply_text("⚠️ No valid data found for this NID.")
        return ConversationHandler.END

    title, desc = fetch_test_title_and_description(nid)
    htmls = {
        "QP_with_Answers.html": generate_html_with_answers(data, title, desc),
        "Only_Answer_Key.html": generate_answer_key_table(data, title, desc),
        "Only_Question_Paper.html": generate_html_only_questions(data, title, desc)
    }

    docs = []
    for filename, html in htmls.items():
        bio = BytesIO(html.encode("utf-8"))
        bio.name = filename
        docs.append(bio)

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

# === HTML Generators ===
def generate_html_with_answers(data, test_title, syllabus):
    """Generate HTML with questions and highlighted correct answers - PDF friendly"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<title>{test_title}</title>
<style>
    body {{
        font-family: Arial, sans-serif;
        background-color: #f2f7ff;
        color: #333;
        padding: 30px;
        line-height: 1.6;
    }}
    .title-box {{
        background: linear-gradient(135deg, #66a3ff 0%, #4da6ff 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(102, 163, 255, 0.3);
        border: 3px solid #3399ff;
        page-break-inside: avoid;
    }}
    .title-box h1 {{
        margin: 0;
        font-size: 28px;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }}
    .question-card {{
        position: relative;
        background: #fff;
        border: 1px solid #b3d1ff;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 30px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
        page-break-inside: avoid;
        break-inside: avoid;
    }}
    .watermark {{
        position: absolute;
        top: 12px;
        right: 14px;
        font-size: 13px;
        font-weight: bold;
        color: #87aade;
        font-family: monospace;
    }}
    .question-watermark {{
        position: absolute;
        top: 8px;
        right: 12px;
        background: rgba(135, 170, 222, 0.15);
        border: 1px solid #87ceeb;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 18px;
        font-weight: bold;
        color: #87ceeb;
        font-family: monospace;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
    }}
    .question-watermark a {{
        color: #87ceeb;
        text-decoration: none;
        font-size: 18px;
        font-weight: bold;
        font-family: monospace;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
    }}
    .question-watermark a:hover {{
        color: #5dade2;
        text-decoration: underline;
    }}
    .question-title {{
        font-size: 20px;
        font-weight: bold;
        color: #004aad;
        margin-bottom: 10px;
    }}
    .question-body {{
        width: 100%;
        display: block;
        white-space: pre-wrap;
        margin-bottom: 15px;
        line-height: 1.4;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}
    .options {{
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-top: 10px;
    }}
    .option-row {{
        display: flex;
        gap: 10px;
        width: 100%;
    }}
    .option {{
        display: flex;
        align-items: flex-start;
        background: #e6f0ff;
        border: 2px solid #cce0ff;
        padding: 12px 16px;
        border-radius: 18px;
        font-size: 15px;
        font-weight: bold;
        text-align: left;
        word-wrap: break-word;
        overflow-wrap: break-word;
        white-space: normal;
        width: 50%;
        box-sizing: border-box;
        min-height: auto;
        page-break-inside: avoid;
        line-height: 1.4;
    }}
    .option.correct {{
        background: #c6f7d0;
        border-color: #50c878;
    }}
    .footer {{
        margin-top: 40px;
        text-align: center;
        font-size: 16px;
        color: #555;
    }}
    .quote {{
        text-align: center;
        margin: 20px 0;
        padding: 20px;
        background: linear-gradient(135deg, #ffb3b3 0%, #ff9999 100%);
        color: white;
        border-radius: 15px;
        font-style: italic;
        font-size: 16px;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        box-shadow: 0 4px 12px rgba(255, 179, 179, 0.3);
        border: 3px solid #ff8080;
        page-break-inside: avoid;
    }}
    .quote-footer {{
        text-align: center;
        margin-top: 30px;
        padding: 15px 20px;
        background: linear-gradient(135deg, #9370db 0%, #8a2be2 100%);
        color: white;
        border-radius: 15px;
        font-style: italic;
        font-size: 16px;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        box-shadow: 0 4px 12px rgba(147, 112, 219, 0.3);
        border: 3px solid #7b68ee;
        display: block;
        max-width: fit-content;
        margin-left: auto;
        margin-right: auto;
        page-break-inside: avoid;
    }}
    .extracted-box {{
        text-align: center;
        margin-top: 15px;
        padding: 12px 18px;
        background: linear-gradient(135deg, #87ceeb 0%, #add8e6 100%);
        color: #2c3e50;
        border-radius: 12px;
        font-size: 15px;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.3);
        box-shadow: 0 3px 10px rgba(135, 206, 235, 0.4);
        border: 2px solid #5dade2;
        display: block;
        max-width: fit-content;
        margin-left: auto;
        margin-right: auto;
        page-break-inside: avoid;
    }}
    
    /* PDF-specific styles */
    @media print {{
        body {{
            background-color: white !important;
            -webkit-print-color-adjust: exact;
            color-adjust: exact;
        }}
        .question-card {{
            page-break-inside: avoid;
            break-inside: avoid;
        }}
        .title-box, .quote, .quote-footer, .extracted-box {{
            page-break-inside: avoid;
        }}
        .option {{
            page-break-inside: avoid;
        }}
    }}
</style>
</head>
<body>
<div class='title-box'>
    <h1>{test_title}</h1>
</div>
<div class='quote'>ᴀ ᴍᴀɴ ᴡʜᴏ ꜱᴛᴀɴᴅꜱ ꜰᴏʀ ɴᴏᴛʜɪɴɢ ᴡɪʟʟ ꜰᴀʟʟ ꜰᴏʀ ᴀɴʏᴛʜɪɴɢ</div>
    """
    for idx, q in enumerate(data, 1):
        processed_body = process_html_content(q['body'])
        html += "<div class='question-card'>"
        html += "<div class='question-watermark'><a href='https://t.me/rockyleakss' target='_blank'>@𝓡𝓞𝑪𝓚𝓨</a></div>"
        html += f"<div class='question-title'>Question {idx}</div>"
        html += f"<div class='question-body'>{processed_body}</div>"
        html += "<div class='options'>"
        
        # Create options in 2 rows with 2 options each
        alternatives = q["alternatives"][:4]  # Limit to first 4 alternatives
        labels = ["A", "B", "C", "D"]
        
        for row in range(2):  # 2 rows
            html += "<div class='option-row'>"
            for col in range(2):  # 2 options per row
                opt_idx = row * 2 + col
                if opt_idx < len(alternatives):
                    opt = alternatives[opt_idx]
                    label = labels[opt_idx]
                    is_correct = str(opt.get("score_if_chosen")) == "1"
                    opt_class = "option correct" if is_correct else "option"
                    processed_answer = process_html_content(opt['answer'])
                    html += f"<div class='{opt_class}'>{label}) {processed_answer}</div>"
            html += "</div>"
        
        html += "</div></div>"
    html += "<div class='quote-footer'>ᴛʜᴇ ᴏɴᴇ ᴀɴᴅ ᴏɴʟʏ ᴘɪᴇᴄᴇ</div>"
    html += "<div class='extracted-box'>Extracted by 『𝗥ᴏᴄ𝗄𝑦』</div></body></html>"
    return html

def generate_html_only_questions(data, test_title, syllabus):
    """Generate HTML with only questions (no answer highlighting) - PDF friendly"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<title>{test_title}</title>
<style>
    body {{
        font-family: Arial, sans-serif;
        background-color: #f2f7ff;
        color: #333;
        padding: 30px;
        line-height: 1.6;
    }}
    .title-box {{
        background: linear-gradient(135deg, #66a3ff 0%, #4da6ff 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(102, 163, 255, 0.3);
        border: 3px solid #3399ff;
        page-break-inside: avoid;
    }}
    .title-box h1 {{
        margin: 0;
        font-size: 28px;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }}
    .question-card {{
        position: relative;
        background: #fff;
        border: 1px solid #b3d1ff;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 30px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
        page-break-inside: avoid;
        break-inside: avoid;
    }}
    .question-watermark {{
        position: absolute;
        top: 8px;
        right: 12px;
        background: rgba(135, 170, 222, 0.15);
        border: 1px solid #87ceeb;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 18px;
        font-weight: bold;
        color: #87ceeb;
        font-family: monospace;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
    }}
    .question-watermark a {{
        color: #87ceeb;
        text-decoration: none;
        font-size: 18px;
        font-weight: bold;
        font-family: monospace;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
    }}
    .question-watermark a:hover {{
        color: #5dade2;
        text-decoration: underline;
    }}
    .question-title {{
        font-size: 20px;
        font-weight: bold;
        color: #004aad;
        margin-bottom: 10px;
    }}
    .question-body {{
        width: 100%;
        display: block;
        white-space: pre-wrap;
        margin-bottom: 15px;
        line-height: 1.4;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}
    .options {{
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-top: 10px;
    }}
    .option-row {{
        display: flex;
        gap: 10px;
        width: 100%;
    }}
    .option {{
        display: flex;
        align-items: flex-start;
        background: #e6f0ff;
        border: 2px solid #cce0ff;
        padding: 12px 16px;
        border-radius: 18px;
        font-size: 15px;
        font-weight: bold;
        text-align: left;
        word-wrap: break-word;
        overflow-wrap: break-word;
        white-space: normal;
        width: 50%;
        box-sizing: border-box;
        min-height: auto;
        page-break-inside: avoid;
        line-height: 1.4;
    }}
    .quote {{
        text-align: center;
        margin: 20px 0;
        padding: 20px;
        background: linear-gradient(135deg, #ffb3b3 0%, #ff9999 100%);
        color: white;
        border-radius: 15px;
        font-style: italic;
        font-size: 16px;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        box-shadow: 0 4px 12px rgba(255, 179, 179, 0.3);
        border: 3px solid #ff8080;
        page-break-inside: avoid;
    }}
    .quote-footer {{
        text-align: center;
        margin-top: 30px;
        padding: 15px 20px;
        background: linear-gradient(135deg, #9370db 0%, #8a2be2 100%);
        color: white;
        border-radius: 15px;
        font-style: italic;
        font-size: 16px;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        box-shadow: 0 4px 12px rgba(147, 112, 219, 0.3);
        border: 3px solid #7b68ee;
        display: block;
        max-width: fit-content;
        margin-left: auto;
        margin-right: auto;
        page-break-inside: avoid;
    }}
    .extracted-box {{
        text-align: center;
        margin-top: 15px;
        padding: 12px 18px;
        background: linear-gradient(135deg, #87ceeb 0%, #add8e6 100%);
        color: #2c3e50;
        border-radius: 12px;
        font-size: 15px;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.3);
        box-shadow: 0 3px 10px rgba(135, 206, 235, 0.4);
        border: 2px solid #5dade2;
        display: block;
        max-width: fit-content;
        margin-left: auto;
        margin-right: auto;
        page-break-inside: avoid;
    }}
    
    /* PDF-specific styles */
    @media print {{
        body {{
            background-color: white !important;
            -webkit-print-color-adjust: exact;
            color-adjust: exact;
        }}
        .question-card {{
            page-break-inside: avoid;
            break-inside: avoid;
        }}
        .title-box, .quote, .quote-footer, .extracted-box {{
            page-break-inside: avoid;
        }}
        .option {{
            page-break-inside: avoid;
        }}
    }}
</style>
</head>
<body>
<div class='title-box'>
    <h1>{test_title}</h1>
</div>
<div class='quote'>ᴀ ᴍᴀɴ ᴡʜᴏ ꜱᴛᴀɴᴅꜱ ꜰᴏʀ ɴᴏᴛʜɪɴɢ ᴡɪʟʟ ꜰᴀʟʟ ꜰᴏʀ ᴀɴʏᴛʜɪɴɢ</div>
    """
    for idx, q in enumerate(data, 1):
        processed_body = process_html_content(q['body'])
        html += "<div class='question-card'>"
        html += "<div class='question-watermark'><a href='https://t.me/rockyleakss' target='_blank'>@𝓡𝓞𝑪𝓚𝓨</a></div>"
        html += f"<div class='question-title'>Question {idx}</div>"
        html += f"<div class='question-body'>{processed_body}</div>"
        html += "<div class='options'>"
        
        # Create options in 2 rows with 2 options each
        alternatives = q["alternatives"][:4]  # Limit to first 4 alternatives
        labels = ["A", "B", "C", "D"]
        
        for row in range(2):  # 2 rows
            html += "<div class='option-row'>"
            for col in range(2):  # 2 options per row
                opt_idx = row * 2 + col
                if opt_idx < len(alternatives):
                    opt = alternatives[opt_idx]
                    label = labels[opt_idx]
                    processed_answer = process_html_content(opt['answer'])
                    html += f"<div class='option'>{label}) {processed_answer}</div>"
            html += "</div>"
        
        html += "</div></div>"
    html += "<div class='quote-footer'>ᴛʜᴇ ᴏɴᴇ ᴀɴᴅ ᴏɴʟʏ ᴘɪᴇᴄᴇ</div>"
    html += "<div class='extracted-box'>Extracted by 『𝗥ᴏᴄ𝗄𝑦』</div></body></html>"
    return html

def generate_answer_key_table(data, test_title, syllabus):
    """Generate HTML with tabular answer key in light bluish theme with reduced size and updated quote/extracted box styles."""
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<title>{test_title} - Answer Key</title>
<style>
    body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background: linear-gradient(135deg, #e3f2fd 0%, #f0f8ff 100%);
        color: #2c3e50;
        padding: 20px; /* Reduced padding */
        line-height: 1.5; /* Slightly reduced line height */
        margin: 0;
        min-height: 100vh;
    }}
    .title-box {{
        background: linear-gradient(135deg, #42a5f5 0%, #1e88e5 100%);
        color: white;
        padding: 20px; /* Reduced padding */
        border-radius: 15px; /* Slightly reduced border-radius */
        text-align: center;
        margin-bottom: 20px; /* Reduced margin */
        box-shadow: 0 6px 20px rgba(66, 165, 245, 0.4); /* Slightly reduced shadow */
        border: 2px solid #2196f3;
    }}
    .title-box h1 {{
        margin: 0;
        font-size: 26px; /* Reduced font size */
        font-weight: 700;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3); /* Slightly reduced shadow */
        letter-spacing: 0.8px; /* Slightly reduced letter-spacing */
    }}
    .answer-key-container {{
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px; /* Slightly reduced border-radius */
        padding: 10px; /* Reduced padding */
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08); /* Slightly reduced shadow */
        margin: 10px 5px; /* Reduced margin */
        border: 1px solid #e1f5fe; /* Reduced border thickness */
        width: calc(100% - 10px); /* Adjusted width */
    }}
    .answer-key-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin: 0;
        background: white;
        box-shadow: 0 3px 10px rgba(33, 150, 243, 0.1); /* Slightly reduced shadow */
        border-radius: 10px; /* Slightly reduced border-radius */
        overflow: hidden;
        font-size: 13px; /* Reduced font size */
        border: 1px solid #2196f3; /* Reduced border thickness */
    }}
    .answer-key-table th {{
        background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
        color: white;
        padding: 10px 8px; /* Reduced padding */
        text-align: center;
        font-weight: 600;
        font-size: 14px; /* Reduced font size */
        border: 1px solid #1976d2;
        text-transform: uppercase;
        letter-spacing: 0.8px; /* Slightly reduced letter-spacing */
        text-shadow: 1px 1px 1px rgba(0, 0, 0, 0.2);
    }}
    .answer-key-table th:first-child {{
        width: 18%;
        border-left: none;
    }}
    .answer-key-table th:nth-child(2) {{
        width: 20%;
    }}
    .answer-key-table th:nth-child(3) {{
        width: 62%;
        border-right: none;
    }}
    .answer-key-table td {{
        padding: 7px 8px; /* Reduced padding */
        text-align: center;
        border: 1px solid #e3f2fd;
        border-top: none;
        font-weight: 500;
        vertical-align: middle;
        transition: background-color 0.3s ease;
    }}
    .answer-key-table tbody tr td:first-child {{
        border-left: none;
    }}
    .answer-key-table tbody tr td:last-child {{
        border-right: none;
    }}
    .answer-key-table tbody tr:last-child td {{
        border-bottom: none;
    }}
    .answer-key-table tbody tr:nth-child(even) {{
        background: linear-gradient(135deg, #f8fdff 0%, #e8f4fd 100%);
    }}
    .answer-key-table tbody tr:nth-child(odd) {{
        background: linear-gradient(135deg, #ffffff 0%, #f5f9ff 100%);
    }}
    .answer-key-table tbody tr:hover {{
        background: linear-gradient(135deg, #e1f5fe 0%, #b3e5fc 100%);
        transform: translateY(-0.5px); /* Slightly reduced transform */
        box-shadow: 0 1px 5px rgba(33, 150, 243, 0.15); /* Slightly reduced shadow */
    }}
    .question-number {{
        font-weight: 700;
        color: #1565c0;
        font-size: 14px; /* Reduced font size */
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 5px 8px; /* Reduced padding */
        border-radius: 5px; /* Slightly reduced border-radius */
        display: inline-block;
        min-width: 30px; /* Reduced min-width */
        border: 1px solid #2196f3;
        margin: 1px; /* Reduced margin */
    }}
    .correct-option {{
        font-weight: 700;
        color: #ffffff;
        font-size: 14px; /* Reduced font size */
        background: linear-gradient(135deg, #42a5f5 0%, #1e88e5 100%);
        padding: 7px 10px; /* Reduced padding */
        border-radius: 5px; /* Slightly reduced border-radius */
        display: inline-block;
        min-width: 30px; /* Reduced min-width */
        box-shadow: 0 1px 5px rgba(66, 165, 245, 0.3); /* Slightly reduced shadow */
        border: 1px solid #1976d2;
        margin: 1px; /* Reduced margin */
    }}
    .answer-text {{
        font-size: 13px; /* Reduced font size */
        color: #37474f;
        text-align: left;
        max-width: 100%;
        word-wrap: break-word;
        line-height: 1.2; /* Slightly reduced line height */
        padding: 4px 6px; /* Reduced padding */
        background: rgba(227, 242, 253, 0.3);
        border-radius: 5px; /* Slightly reduced border-radius */
        border-left: 2px solid #42a5f5; /* Reduced border thickness */
        margin: 0.5px; /* Reduced margin */
    }}
    .quote {{
        text-align: center;
        margin: 20px 0; /* Reduced margin */
        padding: 18px; /* Reduced padding */
        background: #FFFDD0; /* Cream color */
        color: #000000; /* Black font */
        border-radius: 12px; /* Slightly reduced border-radius */
        font-style: italic;
        font-size: 15px; /* Reduced font size */
        font-weight: 600;
        text-shadow: none; /* Removed text shadow */
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); /* Reduced shadow */
        border: 1px solid #e0e0e0; /* Simpler border */
    }}
    .quote-footer {{
        text-align: center;
        margin-top: 30px; /* Reduced margin */
        padding: 12px 18px; /* Reduced padding */
        background: linear-gradient(135deg, #64b5f6 0%, #42a5f5 100%);
        color: white;
        border-radius: 12px; /* Slightly reduced border-radius */
        font-style: italic;
        font-size: 15px; /* Reduced font size */
        font-weight: 600;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        box-shadow: 0 4px 15px rgba(100, 181, 246, 0.3); /* Slightly reduced shadow */
        border: 1px solid #1e88e5; /* Reduced border thickness */
        display: block;
        max-width: fit-content;
        margin-left: auto;
        margin-right: auto;
    }}
    .extracted-box {{
        text-align: center;
        margin-top: 15px; /* Reduced margin */
        padding: 10px 15px; /* Reduced padding */
        background: linear-gradient(135deg, #b3e5fc 0%, #81d4fa 100%);
        color: #0d47a1;
        border-radius: 10px; /* Reduced border-radius */
        font-size: 14px; /* Reduced font size */
        font-weight: 600;
        text-shadow: 1px 1px 1px rgba(255, 255, 255, 0.5); /* Slightly reduced shadow */
        box-shadow: 0 3px 10px rgba(179, 229, 252, 0.4); /* Slightly reduced shadow */
        border: 1px solid #29b6f6; /* Reduced border thickness */
        display: block;
        max-width: fit-content;
        margin-left: auto;
        margin-right: auto;
    }}
    .watermark {{
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(-45deg);
        font-size: 70px; /* Reduced font size */
        color: rgba(66, 165, 245, 0.07); /* Slightly lighter color */
        font-weight: bold;
        z-index: -1;
        pointer-events: none;
    }}

</style>
</head>
<body>
<div class='watermark'>@ROCKY</div>
<div class='title-box'>
    <h1>{test_title}</h1>
    <div style='margin-top: 8px; font-size: 16px; font-weight: 500;'>Answer Key</div>
</div>
<div class='quote'>ᴀ ᴍᴀɴ ᴡʜᴏ ꜱᴛᴀɴᴅꜱ ꜰᴏʀ ɴᴏᴛʜɪɴɢ ᴡɪʟʟ ꜰᴀʟʟ ꜰᴏʀ ᴀɴʏᴛʜɪɴɢ</div>



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
    
    for idx, q in enumerate(data, 1):
        correct_option = ""
        correct_answer = ""
        
        # Find the correct alternative
        for i, opt in enumerate(q["alternatives"][:4]): # Limit to first 4 alternatives
            if str(opt.get("score_if_chosen")) == "1":
                correct_option = ["A", "B", "C", "D"][i]
                correct_answer = process_html_content(opt['answer'])
                break
        
        html += f"""
        <tr>
            <td><span class='question-number'>{idx}</span></td>
            <td><span class='correct-option'>{correct_option}</span></td>
            <td><div class='answer-text'>{correct_answer}</div></td>
        </tr>
        """
    
    html += """
        </tbody>
    </table>
</div>
<div class='quote-footer'>ᴛʜᴇ ᴏɴᴇ ᴀɴᴅ ᴏɴʟʏ ᴘɪᴇᴄᴇ</div>
<div class='extracted-box'>Extracted by 『𝗥ᴏᴄ𝗄𝑦』</div>
</body>
</html>
    """
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
    app.add_handler(conv_handler)

    logger.info("Bot started...")
    app.run_polling()

if __name__ == '__main__':
    main()
