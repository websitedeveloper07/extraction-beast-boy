import os
import json
import requests
from io import BytesIO
import logging
import re
from bs4 import BeautifulSoup
import psutil # For system status

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.error import Conflict
from weasyprint import HTML, CSS # Ensure WeasyPrint is installed and its dependencies are met

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
# IMPORTANT: Replace with your actual bot token from BotFather
BOT_TOKEN = "8163450084:AAFCadeMAzxD6Rb6nfYwJ5Ke5IR8HcCIhWM" 
# IMPORTANT: Replace with your Telegram User ID (numeric) - only this user can authorize/revoke others
OWNER_ID = 7796598050 

# Set to store authorized user IDs. Initialize with the owner's ID.
# This list controls who can use the bot.
AUTHORIZED_USER_IDS = {OWNER_ID}

# Counter for extracted papers
extracted_papers_count = 0

# Define conversation states
ASK_NID = 0 # Only one state needed now as extraction is direct after NID
WAIT_FOR_CHOICE = 1 # State for initial format choice

# --- Helper Functions ---

def is_authorized(user_id):
    """Checks if a user ID is in the set of authorized users."""
    return user_id in AUTHORIZED_USER_IDS

async def send_unauthorized_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends an unauthorized message to users who are not allowed."""
    if update.message:
        await update.message.reply_text("❌ Access Denied. You are not authorized to use this bot.")
    elif update.callback_query:
        await update.callback_query.answer("❌ Access Denied! You are not authorized.", show_alert=True)
        await update.callback_query.message.reply_text("❌ Access Denied. You are not authorized to use this bot.")
    logger.warning(f"Unauthorized access attempt by user ID: {update.effective_user.id}")


def fetch_locale_json_from_api(nid: str):
    """
    Fetches question data from the API for a given NID.
    The API response is expected to be a dictionary where top-level keys are
    individual question NIDs (e.g., "4379498037"), and each of these contains
    language-specific sub-dictionaries (e.g., '843' for English).
    This function extracts all English questions found in the response.
    """
    url = f"https://learn.aakashitutor.com/quiz/{nid}/getlocalequestions"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        raw_data = response.json()
        # Log the full raw data for debugging purposes
        logger.info(f"Raw API response for NID {nid}: {json.dumps(raw_data, indent=2)}")

        processed_questions = []

        def is_valid_question_object(data_obj):
            """
            Checks if a dictionary has the minimum required keys for a question:
            'body' (question text) and 'alternatives' (list of options).
            """
            return isinstance(data_obj, dict) and \
                           "body" in data_obj and \
                           "alternatives" in data_obj and \
                           isinstance(data_obj.get("alternatives"), list)

        # The provided JSON snippet shows raw_data as a dictionary
        # where keys are NIDs (e.g., "4379498037", "4379498039", "4379498041").
        # Each of these NID-keyed objects then contains language-specific data.
        if isinstance(raw_data, dict):
            for question_nid_key, question_data_by_language in raw_data.items():
                if isinstance(question_data_by_language, dict):
                    # We are looking for the English version, which is consistently under the '843' key
                    english_version = question_data_by_language.get("843")
                    
                    if is_valid_question_object(english_version):
                        # Verify it's indeed English, though the '843' key strongly implies it.
                        # The provided JSON shows 'language': ['843'] and 'language_names': ['English']
                        # directly within the '843' object, so we can check those.
                        languages = english_version.get("language", [])
                        language_names = english_version.get("language_names", [])
                        
                        if "843" in languages or "English" in language_names:
                            processed_questions.append({
                                "body": english_version.get("body", ""),
                                "alternatives": english_version.get("alternatives", [])
                            })
                            logger.info(f"NID {nid}: Successfully extracted English question for internal NID {question_nid_key}.")
                        else:
                            logger.warning(f"NID {nid}: Found data under {question_nid_key} -> '843', but it's not explicitly marked as English.")
                    else:
                        logger.warning(f"NID {nid}: No valid question object found under {question_nid_key} -> '843'.")
                else:
                    logger.warning(f"NID {nid}: Content under top-level key '{question_nid_key}' is not a dictionary (expected language mapping).")
        else:
            logger.error(f"NID {nid}: Raw API response is not a dictionary (expected NID mapping). Type: {type(raw_data)}")
            return None # Indicate failure if the top-level structure is wrong

        if not processed_questions:
            logger.error(f"NID {nid}: No English questions extracted from the API response.")

        return processed_questions
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Network error fetching questions for NID {nid}: {req_err}")
        return None
    except json.JSONDecodeError as json_err:
        logger.error(f"JSON decode error for NID {nid}: API returned invalid JSON. Error: {json_err}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred for NID {nid}: {e}", exc_info=True) # exc_info to print traceback
        return None

def fetch_test_title_and_description(nid: str):
    """
    Fetches the test title and description from the API for a given NID.
    """
    url = f"https://learn.aakashitutor.com/api/getquizfromid?nid={nid}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and data:
            item = data[0]
            title = item.get("title", f"Test {nid}").strip()
            description = item.get("description", "").strip()
            return title, description
        return f"Test {nid}", "" # Default title if not found
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching title for NID {nid}: {e}")
        return f"Test {nid}", ""
    except json.JSONDecodeError:
        logger.error(f"JSON decode error for title for NID {nid}: API returned invalid JSON.")
        return f"Test {nid}", ""
    except Exception as e:
        logger.error(f"An unexpected error occurred fetching title for NID {nid}: {e}")
        return f"Test {nid}", ""

def process_html_content(html_string: str) -> str:
    """
    Processes HTML content, specifically fixing protocol-relative image URLs.
    """
    if not html_string:
        return ""
    soup = BeautifulSoup(html_string, 'html.parser')
    for img_tag in soup.find_all('img'):
        src = img_tag.get('src')
        if src and src.startswith('//'):
            # Convert protocol-relative URL to absolute HTTPS URL
            img_tag['src'] = f"https:{src}"
    return str(soup)

# --- HTML Generation Functions (Unchanged as per request) ---
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
        html += "<div class='question-watermark'><a href='https://t.me/rockyleakss' target='_blank'>@𝓡𝓞𝑪𝓚𝓚𝓨</a></div>"
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
        html += "<div class='question-watermark'><a href='https://t.me/rockyleakss' target='_blank'>@𝓡𝓞𝑪𝓚𝓚𝓨</a></div>"
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

# --- Command Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Starts the conversation, displays bot info, and presents format options to authorized users.
    """
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await send_unauthorized_message(update, context)
        return ConversationHandler.END

    message_text = (
        "Hello! I am your document extraction bot.\n\n"
        "Here's what I can do:\n"
        "• Select an option below to extract content from NID.\n"
        "• `/status` - Check the bot's working status and extracted papers count.\n"
        "• `/au <user_id>` - (Owner only) Authorize a user to use this bot.\n"
        "• `/ru <user_id>` - (Owner only) Revoke authorization from a user.\n\n"
        "Please choose the desired output format below:"
    )

    keyboard = [
        [InlineKeyboardButton("📝 QP + Answer Key", callback_data="qp_with_answers")],
        [InlineKeyboardButton("🔑 Only Answer Key", callback_data="only_key")],
        [InlineKeyboardButton("❓ Only Question Paper", callback_data="only_qp")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message_text, reply_markup=reply_markup)
    return WAIT_FOR_CHOICE

async def authorize_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allows the owner to authorize another user."""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Only the bot owner can use this command.")
        return

    if not context.args:
        await update.message.reply_text("Usage: `/au <user_id>`\nExample: `/au 123456789`", parse_mode='Markdown')
        return

    try:
        user_id_to_authorize = int(context.args[0])
        if user_id_to_authorize not in AUTHORIZED_USER_IDS:
            AUTHORIZED_USER_IDS.add(user_id_to_authorize)
            await update.message.reply_text(f"✅ User ID `{user_id_to_authorize}` has been authorized.", parse_mode='Markdown')
            logger.info(f"User ID {user_id_to_authorize} authorized by {update.effective_user.id}")
        else:
            await update.message.reply_text(f"❕ User ID `{user_id_to_authorize}` is already authorized.", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("❌ Invalid User ID. Please provide a numerical ID.")
    except Exception as e:
        logger.error(f"Error in authorize_user: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while trying to authorize the user.")

async def revoke_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allows the owner to revoke authorization from a user."""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Only the bot owner can use this command.")
        return

    if not context.args:
        await update.message.reply_text("Usage: `/ru <user_id>`\nExample: `/ru 123456789`", parse_mode='Markdown')
        return

    try:
        user_id_to_revoke = int(context.args[0])
        if user_id_to_revoke == OWNER_ID:
            await update.message.reply_text("🚫 You cannot revoke authorization from yourself (the owner).")
            return

        if user_id_to_revoke in AUTHORIZED_USER_IDS:
            AUTHORIZED_USER_IDS.remove(user_id_to_revoke)
            await update.message.reply_text(f"🗑️ User ID `{user_id_to_revoke}` has had their authorization revoked.", parse_mode='Markdown')
            logger.info(f"User ID {user_id_to_revoke} revoked by {update.effective_user.id}")
        else:
            await update.message.reply_text(f"❕ User ID `{user_id_to_revoke}` is not currently authorized.", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("❌ Invalid User ID. Please provide a numerical ID.")
    except Exception as e:
        logger.error(f"Error in revoke_user: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while trying to revoke authorization.")


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the user's format choice from the inline keyboard.
    """
    if not is_authorized(update.effective_user.id):
        await send_unauthorized_message(update, context)
        return ConversationHandler.END

    query = update.callback_query
    await query.answer() # Acknowledge the callback query

    context.user_data['mode'] = query.data
    
    # Directly ask for NID after format selection
    await query.edit_message_text("🔢 Please send the NID (Numerical ID) for the test you want to extract:")
    return ASK_NID

async def handle_nid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receives the NID from the user and performs all extractions.
    """
    if not is_authorized(update.effective_user.id):
        await send_unauthorized_message(update, context)
        return ConversationHandler.END

    nid = update.message.text.strip()
    if not nid.isdigit():
        await update.message.reply_text("❌ Invalid NID. Please send a numerical ID.")
        return ASK_NID # Stay in this state until a valid NID is provided

    await update.message.reply_text("🚀 Fetching data and generating files... This may take a moment.")
    
    global extracted_papers_count

    try:
        data = fetch_locale_json_from_api(nid)
        if not data:
            await update.message.reply_text("⚠️ Could not retrieve question data for the provided NID. Please check the NID or try again later.")
            return ConversationHandler.END # End conversation

        test_title, syllabus = fetch_test_title_and_description(nid)

        # --- Generate and Send all formats ---
        # 1. QP + Answer Key (PDF)
        html_qp_answers = generate_html_with_answers(data, test_title, syllabus)
        qp_answers_pdf_file = BytesIO()
        HTML(string=html_qp_answers).write_pdf(qp_answers_pdf_file)
        qp_answers_pdf_file.seek(0)
        await update.message.reply_document(
            qp_answers_pdf_file,
            filename=f"{test_title}_QP_with_Answers.pdf",
            caption="📝 Question Paper with Answer Key (PDF)"
        )
        logger.info(f"Sent QP with Answers PDF for NID {nid}")

        # 2. Only Answer Key (PDF)
        html_only_key = generate_answer_key_table(data, test_title, syllabus)
        only_key_pdf_file = BytesIO()
        HTML(string=html_only_key).write_pdf(only_key_pdf_file)
        only_key_pdf_file.seek(0)
        await update.message.reply_document(
            only_key_pdf_file,
            filename=f"{test_title}_Only_Answer_Key.pdf",
            caption="🔑 Only Answer Key (PDF)"
        )
        logger.info(f"Sent Only Answer Key PDF for NID {nid}")

        # 3. Only Question Paper (PDF)
        html_only_qp = generate_html_only_questions(data, test_title, syllabus)
        only_qp_pdf_file = BytesIO()
        HTML(string=html_only_qp).write_pdf(only_qp_pdf_file)
        only_qp_pdf_file.seek(0)
        await update.message.reply_document(
            only_qp_pdf_file,
            filename=f"{test_title}_Only_Question_Paper.pdf",
            caption="❓ Only Question Paper (PDF)"
        )
        logger.info(f"Sent Only Question Paper PDF for NID {nid}")
        
        extracted_papers_count += 1
        await update.message.reply_text(
            "✅ All requested formats have been extracted and sent!"
        )

    except Exception as e:
        logger.error(f"Error during extraction for NID {nid}: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ An error occurred during extraction. Please ensure the NID is correct and try again.\nError: `{html.escape(str(e))}`"
        , parse_mode='Markdown')
    
    return ConversationHandler.END # End the conversation after sending files

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays bot status including extracted papers count, CPU, and RAM usage."""
    if not is_authorized(update.effective_user.id):
        await send_unauthorized_message(update, context)
        return

    try:
        cpu_usage = psutil.cpu_percent(interval=1) # Measures CPU usage over 1 second
        ram_info = psutil.virtual_memory()
        ram_total_gb = round(ram_info.total / (1024**3), 2)
        ram_used_gb = round(ram_info.used / (1024**3), 2)
        ram_percent = ram_info.percent

        status_message = (
            f"📊 **Bot Status**\n"
            f"• Papers extracted: `{extracted_papers_count}`\n"
            f"• CPU Usage: `{cpu_usage}%`\n"
            f"• RAM Usage: `{ram_percent}%` (`{ram_used_gb}` GB / `{ram_total_gb}` GB)\n"
            f"• Authorized Users: `{len(AUTHORIZED_USER_IDS)}`\n\n"
            f"Authorized User IDs (Owner View): `{list(AUTHORIZED_USER_IDS)}`"
        )
        await update.message.reply_text(status_message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error fetching status: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Could not retrieve status information. Error: `{html.escape(str(e))}`", parse_mode='Markdown')

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responds to unknown commands or general text messages if not in a conversation state."""
    if not is_authorized(update.effective_user.id):
        await send_unauthorized_message(update, context)
        return

    if update.message.text and update.message.text.startswith('/'):
        await update.message.reply_text("🤷‍♂️ Sorry, I don't understand that command. Please use /start for available options.")
    else:
        # If not a command and not expecting NID, do nothing or provide general help
        # This prevents the bot from constantly replying to non-command messages when not in a conversation.
        pass

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log the error and send a message to the user."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update.effective_message:
        await update.effective_message.reply_text(
            "An unexpected error occurred while processing your request. Please try again later or contact the bot administrator."
        )

def main():
    """Start the bot."""
    # Create the Application and pass your bot's token.
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Conversation Handler for /start -> format choice -> NID input
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            WAIT_FOR_CHOICE: [CallbackQueryHandler(handle_callback_query)],
            ASK_NID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_nid)],
        },
        fallbacks=[
            # This handler will catch any command during the conversation and tell the user to complete current task or restart.
            # You might want more specific fallbacks or allow certain commands during conversation.
            MessageHandler(filters.COMMAND, unknown_command_in_conv),
            MessageHandler(filters.TEXT & ~filters.COMMAND, unexpected_text_in_conv)
        ],
        allow_reentry=True # Allows users to restart the conversation with /start
    )

    application.add_handler(conv_handler)

    # General Command Handlers (outside the conversation flow)
    # These handlers will only trigger if a conversation is NOT active or if `fallbacks` redirect to them.
    application.add_handler(CommandHandler("au", authorize_user))
    application.add_handler(CommandHandler("ru", revoke_user))
    application.add_handler(CommandHandler("status", status_command))
    
    # Generic handler for unknown commands or messages not caught by specific handlers (must be last)
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown)) # Catch any other text

    # Error handler
    application.add_error_handler(error_handler)

    # Function to handle unknown commands within a conversation
    async def unknown_command_in_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_authorized(update.effective_user.id):
            await send_unauthorized_message(update, context)
            return ConversationHandler.END
        await update.message.reply_text("Please complete the current task or use /start to restart.")

    # Function to handle unexpected text within a conversation
    async def unexpected_text_in_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_authorized(update.effective_user.id):
            await send_unauthorized_message(update, context)
            return ConversationHandler.END
        await update.message.reply_text("I'm expecting a numerical ID. Please provide the NID or use /start to cancel.")


    # Run the bot until you press Ctrl-C
    logger.info("Bot started polling...")
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Conflict:
        logger.warning("Conflict error: Another bot instance is likely running. Please ensure only one instance is active.")
    except Exception as e:
        logger.critical(f"Unhandled exception in main application loop: {e}", exc_info=True)

if __name__ == '__main__':
    main()
