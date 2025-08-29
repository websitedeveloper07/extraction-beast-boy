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


def generate_html_with_answers(data, test_title, syllabus): """Generate HTML with questions and highlighted correct answers - Enhanced Vibrant Layout with Image Support""" html = f""" <!DOCTYPE html> <html> <head> <meta charset='UTF-8'> <title>{test_title}</title> <script src="https://cdn.js

pasted

I can see you have a well-structured HTML generator function for creating test/quiz layouts with questions and answers. This code creates a beautiful, modern interface with gradient backgrounds, proper styling, and support for images in both questions and answer options.

Here are some key features I notice in your code:

Strengths:

Modern, responsive design with beautiful gradients and hover effects
Print-friendly CSS for PDF generation
Image support for both questions and options with error handling
Mobile-responsive layout
Professional styling with custom fonts and animations
Proper semantic HTML structure
MathJax support for mathematical content
Potential Improvements:

Accessibility: Consider adding ARIA labels and keyboard navigation support
Error Handling: The image error handling could be enhanced with retry mechanisms
Performance: Image lazy loading could improve page load times
Security: Consider sanitizing HTML content to prevent XSS attacks
Would you like me to:

Enhance the existing code with additional features?
Create a demo version showing how it works?
Optimize it for better performance or accessibility?
Add new functionality like question filtering, search, or analytics?
What specific improvements or modifications would you like to make to this quiz generator?


def generate_answer_key_table(data, test_title, syllabus): """Generate HTML answer key table - Modern Premium theme (with MathJax & image support)""" html = f""" <!DOCTYPE html> <html> <head> <meta charset='UTF-8'> <title>{test_title} - Answer Key</title> <style> @import url('https://fon

pasted

make this answer key layout as the above i sended you match it to that

I can see you want to update the answer key layout to match the modern, vibrant style of the quiz layout you showed me earlier. Let me create a matching design that maintains consistency between both components.


Updated Answer Key Generator - Matching Quiz Style
Code 
I've completely redesigned the answer key generator to match the vibrant, modern style of your quiz layout. Here are the key improvements:

✨ Matching Design Elements:
Visual Consistency:
Same gradient backgrounds (
#f5f7fa to 
#c3cfe2)
Matching header design with gradient (
#667eea to 
#764ba2)
Identical quote section with orange gradient styling
Consistent color scheme and typography (Inter + Poppins fonts)
Enhanced Features:
Grid-based table layout instead of traditional HTML table
Hover effects with smooth animations and transforms
Responsive design that adapts beautifully to mobile devices
Enhanced image support with error handling and placeholders
Print-friendly CSS for PDF generation
Style Improvements:
Modern card design with rounded corners and shadows
Vibrant button styling for question numbers and correct options
Gradient backgrounds for answer text cells
Consistent spacing and typography throughout
Key Matching Elements:
Header: Same gradient, typography, and watermark placement
Quote section: Identical orange gradient with decorative quotes
Color palette: Blue gradients for primary elements, green for correct answers
Footer: Same styling with signature block
Mobile responsiveness: Maintains usability on all screen sizes
The answer key now perfectly complements your quiz layout while providing a clean, professional way to display correct answers and explanations. The design maintains the same premium feel and visual hierarchy as the original quiz interface.

reduce size and remove the @harsh from it and decrease size of test header box and font


Updated Answer Key Generator - Matching Quiz Style
Code ∙ Version 2 

Updated Answer Key Generator - Matching Quiz Style
Code ∙ Version 3 

Updated Answer Key Generator - Matching Quiz Style
Code ∙ Version 4 

Updated Answer Key Generator - Matching Quiz Style
Code ∙ Version 5 

Updated Answer Key Generator - Matching Quiz Style
Code ∙ Version 6 

Updated Answer Key Generator - Matching Quiz Style
Code ∙ Version 7 

Updated Answer Key Generator - Matching Quiz Style
Code ∙ Version 8 

Updated Answer Key Generator - Matching Quiz Style
Code ∙ Version 9 

Updated Answer Key Generator - Matching Quiz Style
Code ∙ Version 10 
Perfect! I've made all the requested changes:

✅ Changes Made:
Size Reductions:
Container width: Reduced from 1200px to 900px
Border radius: Reduced from 16px to 12px
Box shadow: Made more subtle (15px instead of 20px)
Header Size Reduction:
Padding: Reduced from 25px to 15px (top/bottom)
Font size: Reduced from 28px to 22px
Font weight: Reduced from 700 to 600
Subtitle: Reduced from 14px to 12px
Quote Section:
Padding: Reduced from 18px to 12px
Font size: Reduced from 16px to 14px
@Harsh Removal:
Watermark link: Completely removed from header
CSS styles: Cleaned up watermark-related styles
Mobile styles: Removed watermark positioning code
Mobile Optimization:
Quote text: Further reduced to 12px on mobile
Quote padding: Reduced to 15px on mobile
The answer key layout is now more compact and cleaner without the @Harsh branding, while maintaining all the visual appeal and functionality. The header is significantly smaller and more proportioned for better content-to-header ratio.

make test box fon and size more small


Updated Answer Key Generator - Matching Quiz Style
Code ∙ Version 11 

Updated Answer Key Generator - Matching Quiz Style
Code ∙ Version 12 

Updated Answer Key Generator - Matching Quiz Style
Code ∙ Version 13 

Updated Answer Key Generator - Matching Quiz Style
Code ∙ Version 14 
Perfect! I've made the test header box even smaller with these changes:

✅ Additional Size Reductions:
Header Box:
Padding: Further reduced from 15px to 12px
Title font size: Reduced from 22px to 18px (desktop) and 24px to 16px (mobile)
Font family: Changed from Poppins to Inter (more compact)
Font weight: Reduced from 600 to 500
Text shadow: Made more subtle (1px instead of 2px)
Subtitle:
Font size: Reduced from 12px to 11px
Margin: Reduced from 4px to 2px
Opacity: Slightly reduced from 0.9 to 0.85
Font weight: Added 400 for lighter appearance
The header is now much more compact and takes up minimal space while still maintaining readability and visual appeal. The overall header box is now significantly smaller than the original design.

give proper full the test name and box should be small


Updated Answer Key Generator - Matching Quiz Style
Code ∙ Version 15 
Perfect! Now the header displays the full test name properly with a much more compact design:

✅ Changes Made:
Header Content:
Title: Now shows the complete {test_title} without "- Answer Key" appended
Subtitle: Simplified to just "Answer Key" instead of the long phrase
Result:
Compact box: The header is now much smaller and cleaner
Full test name: The complete test title will be displayed properly
Clean layout: Simple "Answer Key" subtitle keeps it minimal
The header box is now significantly smaller while still showing the full test name clearly. The design is much more compact and professional.

ok now i want to add this image -
https://i.postimg.cc/DwqS1pxt/image-removebg-preview-1.png

to each page as a logo in ccentre diagnolly and little transparent 5%


Updated Answer Key Generator - Matching Quiz Style
Code ∙ Version 16 

Updated Answer Key Generator - Matching Quiz Style
Code ∙ Version 17 

Updated Answer Key Generator - Matching Quiz Style
Code ∙ Version 18 
Perfect! I've added the watermark logo with the following specifications:

✅ Logo Watermark Added:
Positioning:
Fixed center position: Positioned at 50% from top and left
Diagonal rotation: 45-degree rotation for professional watermark effect
Size: 300px x 300px for good visibility without being intrusive
Transparency & Layering:
5% opacity: Set to opacity: 0.05 as requested
Behind content: z-index: 0 ensures it stays behind all content
Non-interactive: pointer-events: none prevents interference with user interaction
Responsive Features:
Fixed positioning: Stays centered regardless of scroll
Print optimized: Even more subtle (3% opacity) when printing
Background sizing: Uses contain to maintain aspect ratio
Visual Effect:
The logo appears as a subtle diagonal watermark in the center of every page
It's transparent enough to not interfere with readability
Maintains professional appearance while providing brand presence
The watermark will now appear on every page as a subtle, diagonal, centered logo with 5% transparency, exactly as you requested!

the images in the html are not properly showned

You're right! The images in the HTML are likely not displaying properly. Let me fix the image handling in the answer key generator:


Drafting artifact...
 




def generate_answer_key_table(data, test_title, syllabus):
    """Generate HTML answer key table - Matching the vibrant quiz layout style"""
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
    }}

    .container {{
        max-width: 1200px;
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
    
    .answer-key-container {{
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
        
        .answer-key-table {{
            box-shadow: none;
        }}
        
        .answer-row:hover {{
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
    }}

    .answer-key-table {{
        width: 100%;
        background: #ffffff;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        border: 2px solid #e2e8f0;
    }}

    .table-header {{
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        display: grid;
        grid-template-columns: 120px 120px 1fr;
        gap: 0;
    }}

    .table-header-cell {{
        padding: 18px 15px;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 14px;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-right: 1px solid rgba(255, 255, 255, 0.2);
    }}

    .table-header-cell:last-child {{
        border-right: none;
        text-align: left;
    }}

    .answer-row {{
        display: grid;
        grid-template-columns: 120px 120px 1fr;
        gap: 0;
        border-bottom: 1px solid #e2e8f0;
        transition: all 0.3s ease;
        background: #ffffff;
    }}

    .answer-row:nth-child(even) {{
        background: #f8fafc;
    }}

    .answer-row:hover {{
        background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
    }}

    .answer-cell {{
        padding: 16px 15px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-right: 1px solid #e2e8f0;
        min-height: 60px;
    }}

    .answer-cell:last-child {{
        border-right: none;
        justify-content: flex-start;
        text-align: left;
    }}
    
    .question-number {{
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: 700;
        border-radius: 15px;
        box-shadow: 0 3px 8px rgba(66, 153, 225, 0.25);
        min-width: 50px;
        text-align: center;
    }}
    
    .correct-option {{
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: 700;
        border-radius: 15px;
        box-shadow: 0 3px 8px rgba(72, 187, 120, 0.25);
        min-width: 50px;
        text-align: center;
        position: relative;
    }}

    .correct-option::before {{
        content: '✓';
        margin-right: 4px;
        font-size: 12px;
    }}
    
    .answer-text {{
        color: #2d3748;
        font-weight: 500;
        line-height: 1.6;
        padding: 8px 12px;
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        border-radius: 8px;
        border-left: 3px solid #667eea;
        margin: 4px 0;
        min-height: 40px;
        display: flex;
        align-items: center;
        flex: 1;
    }}

    .answer-image {{
        max-width: 200px;
        max-height: 100px;
        width: auto;
        height: auto;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        margin: 5px 0;
    }}

    .image-placeholder {{
        background: #f7fafc;
        border: 2px dashed #cbd5e0;
        border-radius: 6px;
        padding: 15px;
        text-align: center;
        color: #a0aec0;
        font-style: italic;
        margin: 5px 0;
        font-size: 12px;
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

    .watermark-link {{
        position: absolute;
        top: 15px;
        right: 20px;
        background: linear-gradient(135deg, #fc8181 0%, #e53e3e 100%);
        color: white;
        padding: 5px 12px;
        font-size: 11px;
        font-weight: 600;
        border-radius: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 6px rgba(252, 129, 129, 0.25);
        text-decoration: none;
        z-index: 2;
    }}
    
    @media (max-width: 768px) {{
        body {{ padding: 15px; }}
        .container {{ margin: 0; }}
        .header {{ padding: 30px 20px; }}
        .header h1 {{ font-size: 24px; }}
        .answer-key-container {{ padding: 15px; }}
        
        .table-header,
        .answer-row {{
            grid-template-columns: 1fr;
            gap: 10px;
        }}
        
        .table-header-cell,
        .answer-cell {{
            border-right: none;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            text-align: center;
            justify-content: center;
        }}
        
        .table-header-cell:last-child,
        .answer-cell:last-child {{
            border-bottom: none;
        }}
        
        .answer-text {{ margin: 8px 0; }}
        .quote-section {{ padding: 20px; }}
        .quote-text {{ font-size: 14px; }}
        
        .watermark-link {{
            position: relative;
            top: auto;
            right: auto;
            display: block;
            margin: 10px auto 0;
            width: fit-content;
        }}
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
        <div class='answer-key-table'>
            <div class='table-header'>
                <div class='table-header-cell'>Question No.</div>
                <div class='table-header-cell'>Correct Option</div>
                <div class='table-header-cell'>Answer Text</div>
            </div>
"""
    
    for idx, q in enumerate(data, 1):
        correct_option = ""
        correct_answer = ""
        
        # Find the correct answer
        for i, opt in enumerate(q.get("alternatives", [])[:4]):
            if str(opt.get("score_if_chosen")) == "1":
                correct_option = ["A", "B", "C", "D"][i]
                
                # Handle both text and image content
                correct_answer = opt.get('answer') or ""
                
                # Enhanced image handling for answers
                if not correct_answer and opt.get("image"):
                    image_url = opt['image']
                    correct_answer = f"<img src='{image_url}' alt='Answer {correct_option}' class='answer-image' onerror=\"this.style.display='none'; this.nextElementSibling.style.display='block';\" /><div class='image-placeholder' style='display:none;'>Image not available</div>"
                elif opt.get("image"):
                    image_url = opt['image']
                    correct_answer += f"<br><img src='{image_url}' alt='Answer {correct_option}' class='answer-image' onerror=\"this.style.display='none'; this.nextElementSibling.style.display='block';\" /><div class='image-placeholder' style='display:none;'>Image not available</div>"
                
                break
        
        html += f"""
            <div class='answer-row'>
                <div class='answer-cell'>
                    <span class='question-number'>{idx}</span>
                </div>
                <div class='answer-cell'>
                    <span class='correct-option'>{correct_option}</span>
                </div>
                <div class='answer-cell'>
                    <div class='answer-text'>{correct_answer}</div>
                </div>
            </div>"""
    
    html += """
        </div>
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
    """Generate HTML answer key table - Matching the vibrant quiz layout style"""
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
    }}

    .container {{
        max-width: 1200px;
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
    
    .answer-key-container {{
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
        
        .answer-key-table {{
            box-shadow: none;
        }}
        
        .answer-row:hover {{
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
    }}

    .answer-key-table {{
        width: 100%;
        background: #ffffff;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        border: 2px solid #e2e8f0;
    }}

    .table-header {{
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        display: grid;
        grid-template-columns: 120px 120px 1fr;
        gap: 0;
    }}

    .table-header-cell {{
        padding: 18px 15px;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 14px;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-right: 1px solid rgba(255, 255, 255, 0.2);
    }}

    .table-header-cell:last-child {{
        border-right: none;
        text-align: left;
    }}

    .answer-row {{
        display: grid;
        grid-template-columns: 120px 120px 1fr;
        gap: 0;
        border-bottom: 1px solid #e2e8f0;
        transition: all 0.3s ease;
        background: #ffffff;
    }}

    .answer-row:nth-child(even) {{
        background: #f8fafc;
    }}

    .answer-row:hover {{
        background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
    }}

    .answer-cell {{
        padding: 16px 15px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-right: 1px solid #e2e8f0;
        min-height: 60px;
    }}

    .answer-cell:last-child {{
        border-right: none;
        justify-content: flex-start;
        text-align: left;
    }}
    
    .question-number {{
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: 700;
        border-radius: 15px;
        box-shadow: 0 3px 8px rgba(66, 153, 225, 0.25);
        min-width: 50px;
        text-align: center;
    }}
    
    .correct-option {{
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: 700;
        border-radius: 15px;
        box-shadow: 0 3px 8px rgba(72, 187, 120, 0.25);
        min-width: 50px;
        text-align: center;
        position: relative;
    }}

    .correct-option::before {{
        content: '✓';
        margin-right: 4px;
        font-size: 12px;
    }}
    
    .answer-text {{
        color: #2d3748;
        font-weight: 500;
        line-height: 1.6;
        padding: 8px 12px;
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        border-radius: 8px;
        border-left: 3px solid #667eea;
        margin: 4px 0;
        min-height: 40px;
        display: flex;
        align-items: center;
        flex: 1;
    }}

    .answer-image {{
        max-width: 200px;
        max-height: 100px;
        width: auto;
        height: auto;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        margin: 5px 0;
    }}

    .image-placeholder {{
        background: #f7fafc;
        border: 2px dashed #cbd5e0;
        border-radius: 6px;
        padding: 15px;
        text-align: center;
        color: #a0aec0;
        font-style: italic;
        margin: 5px 0;
        font-size: 12px;
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

    .watermark-link {{
        position: absolute;
        top: 15px;
        right: 20px;
        background: linear-gradient(135deg, #fc8181 0%, #e53e3e 100%);
        color: white;
        padding: 5px 12px;
        font-size: 11px;
        font-weight: 600;
        border-radius: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 6px rgba(252, 129, 129, 0.25);
        text-decoration: none;
        z-index: 2;
    }}
    
    @media (max-width: 768px) {{
        body {{ padding: 15px; }}
        .container {{ margin: 0; }}
        .header {{ padding: 30px 20px; }}
        .header h1 {{ font-size: 24px; }}
        .answer-key-container {{ padding: 15px; }}
        
        .table-header,
        .answer-row {{
            grid-template-columns: 1fr;
            gap: 10px;
        }}
        
        .table-header-cell,
        .answer-cell {{
            border-right: none;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            text-align: center;
            justify-content: center;
        }}
        
        .table-header-cell:last-child,
        .answer-cell:last-child {{
            border-bottom: none;
        }}
        
        .answer-text {{ margin: 8px 0; }}
        .quote-section {{ padding: 20px; }}
        .quote-text {{ font-size: 14px; }}
        
        .watermark-link {{
            position: relative;
            top: auto;
            right: auto;
            display: block;
            margin: 10px auto 0;
            width: fit-content;
        }}
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
        <div class='answer-key-table'>
            <div class='table-header'>
                <div class='table-header-cell'>Question No.</div>
                <div class='table-header-cell'>Correct Option</div>
                <div class='table-header-cell'>Answer Text</div>
            </div>
"""
    
    for idx, q in enumerate(data, 1):
        correct_option = ""
        correct_answer = ""
        
        # Find the correct answer
        for i, opt in enumerate(q.get("alternatives", [])[:4]):
            if str(opt.get("score_if_chosen")) == "1":
                correct_option = ["A", "B", "C", "D"][i]
                
                # Handle both text and image content
                correct_answer = opt.get('answer') or ""
                
                # Enhanced image handling for answers
                if not correct_answer and opt.get("image"):
                    image_url = opt['image']
                    correct_answer = f"<img src='{image_url}' alt='Answer {correct_option}' class='answer-image' onerror=\"this.style.display='none'; this.nextElementSibling.style.display='block';\" /><div class='image-placeholder' style='display:none;'>Image not available</div>"
                elif opt.get("image"):
                    image_url = opt['image']
                    correct_answer += f"<br><img src='{image_url}' alt='Answer {correct_option}' class='answer-image' onerror=\"this.style.display='none'; this.nextElementSibling.style.display='block';\" /><div class='image-placeholder' style='display:none;'>Image not available</div>"
                
                break
        
        html += f"""
            <div class='answer-row'>
                <div class='answer-cell'>
                    <span class='question-number'>{idx}</span>
                </div>
                <div class='answer-cell'>
                    <span class='correct-option'>{correct_option}</span>
                </div>
                <div class='answer-cell'>
                    <div class='answer-text'>{correct_answer}</div>
                </div>
            </div>"""
    
    html += """
        </div>
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
