from bs4 import BeautifulSoup

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
    """Generate HTML with questions and highlighted correct answers - Modern Premium theme"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<title>{test_title}</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    
    body {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: radial-gradient(circle at 20% 50%, #120078 0%, #000000 50%, #1a0033 100%);
        background-attachment: fixed;
        color: #f8fafc;
        padding: 24px;
        line-height: 1.7;
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
        background: url('data:image/svg+xml,<svg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd"><circle fill="%23ffffff" fill-opacity="0.02" cx="30" cy="30" r="1"/></g></svg>');
        z-index: -1;
        opacity: 0.4;
    }}
    
    .title-box {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        backdrop-filter: blur(20px);
        padding: 32px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 32px;
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1);
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
        font-size: 32px;
        font-weight: 700;
        background: linear-gradient(135deg, #ffffff 0%, #e0e7ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: none;
        margin: 0;
    }}
    
    .question-card {{
        position: relative;
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.05);
        transition: all 0.3s ease;
        overflow: hidden;
    }}
    
    .question-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        border-radius: 16px 16px 0 0;
    }}
    
    .question-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.1);
    }}
    
    .question-watermark {{
        position: absolute;
        top: 16px;
        right: 16px;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(102, 126, 234, 0.3);
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        color: #a5b4fc;
        font-family: 'Inter', monospace;
        z-index: 2;
    }}
    
    .question-watermark a {{
        color: #a5b4fc;
        text-decoration: none;
        transition: color 0.3s ease;
    }}
    
    .question-watermark a:hover {{
        color: #c7d2fe;
    }}
    
    .question-title {{
        font-size: 20px;
        font-weight: 600;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 16px;
        margin-top: 8px;
    }}
    
    .question-body {{
        color: #cbd5e1;
        margin-bottom: 20px;
        white-space: pre-wrap;
        word-wrap: break-word;
        font-weight: 400;
        line-height: 1.6;
    }}
    
    .options {{
        display: flex;
        flex-direction: column;
        gap: 12px;
    }}
    
    .option-row {{
        display: flex;
        gap: 12px;
    }}
    
    .option {{
        background: linear-gradient(135deg, rgba(51, 65, 85, 0.6) 0%, rgba(30, 41, 59, 0.6) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(148, 163, 184, 0.2);
        padding: 14px 18px;
        border-radius: 12px;
        font-size: 14px;
        font-weight: 500;
        color: #e2e8f0;
        width: 50%;
        box-sizing: border-box;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }}
    
    .option:hover {{
        background: linear-gradient(135deg, rgba(71, 85, 105, 0.7) 0%, rgba(51, 65, 85, 0.7) 100%);
        border-color: rgba(148, 163, 184, 0.4);
        transform: translateY(-1px);
    }}
    
    .option.correct {{
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        border-color: #34d399;
        color: #ffffff;
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4), 0 0 0 1px rgba(52, 211, 153, 0.2);
        font-weight: 600;
    }}
    
    .option.correct::before {{
        content: '✓';
        position: absolute;
        top: 8px;
        right: 12px;
        font-weight: bold;
        font-size: 16px;
        color: #ffffff;
    }}
    
    .quote {{
        text-align: center;
        margin: 32px auto;
        padding: 24px 32px;
        background: linear-gradient(135deg, rgba(251, 191, 36, 0.1) 0%, rgba(245, 158, 11, 0.1) 100%);
        backdrop-filter: blur(20px);
        color: #fbbf24;
        border-radius: 16px;
        font-style: italic;
        font-size: 18px;
        font-weight: 500;
        box-shadow: 0 10px 30px rgba(251, 191, 36, 0.2), 0 0 0 1px rgba(251, 191, 36, 0.2);
        border: 1px solid rgba(251, 191, 36, 0.3);
        max-width: 600px;
        position: relative;
    }}
    
    .quote::before {{
        content: '"';
        position: absolute;
        top: -10px;
        left: 20px;
        font-size: 60px;
        color: rgba(251, 191, 36, 0.3);
        font-family: serif;
    }}
    
    .quote-footer, .extracted-box {{
        text-align: center;
        margin: 24px auto;
        padding: 16px 24px;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
        backdrop-filter: blur(20px);
        color: #a5b4fc;
        border-radius: 12px;
        font-weight: 600;
        font-size: 14px;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.2), 0 0 0 1px rgba(102, 126, 234, 0.2);
        border: 1px solid rgba(102, 126, 234, 0.3);
        max-width: fit-content;
    }}
    
    .extracted-box {{
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(109, 40, 217, 0.2) 100%);
        color: #c4b5fd;
        border-color: rgba(139, 92, 246, 0.3);
        box-shadow: 0 8px 20px rgba(139, 92, 246, 0.2), 0 0 0 1px rgba(139, 92, 246, 0.2);
    }}
    
    @media print {{
        body {{ 
            background: #000 !important; 
            -webkit-print-color-adjust: exact;
        }}
        .question-card {{ 
            page-break-inside: avoid; 
            background: #1e293b !important;
        }}
    }}
    
    @media (max-width: 768px) {{
        body {{ padding: 16px; }}
        .title-box {{ padding: 24px 20px; }}
        .title-box h1 {{ font-size: 24px; }}
        .question-card {{ padding: 20px; }}
        .option-row {{ flex-direction: column; }}
        .option {{ width: 100%; }}
    }}
</style>
</head>
<body>
<div class='title-box'>
    <h1>{test_title}</h1>
</div>
<div class='quote'>🌟 "𝙏𝙝𝙚 𝙤𝙣𝙡𝙮 𝙞𝙢𝙥𝙤𝙨𝙨𝙞𝙗𝙡𝙚 𝙟𝙤𝙪𝙧𝙣𝙚𝙮 𝙞𝙨 𝙩𝙝𝙚 𝙤𝙣𝙚 𝙮𝙤𝙪 𝙣𝙚𝙫𝙚𝙧 𝙗𝙚𝙜𝙞𝙣" ✨</div>
"""
    
    for idx, q in enumerate(data, 1):
        processed_body = process_html_content(q['body'])
        html += f"""
<div class='question-card'>
    <div class='question-watermark'><a href='https://t.me/rockyleakss' target='_blank'>@𝓗𝓐𝓡𝓢𝓗</a></div>
    <div class='question-title'>Question {idx}</div>
    <div class='question-body'>{processed_body}</div>
    <div class='options'>"""
        
        alternatives = q["alternatives"][:4]
        labels = ["A", "B", "C", "D"]
        
        for row in range(2):
            html += "<div class='option-row'>"
            for col in range(2):
                opt_idx = row * 2 + col
                if opt_idx < len(alternatives):
                    opt = alternatives[opt_idx]
                    is_correct = str(opt.get("score_if_chosen")) == "1"
                    class_name = "option correct" if is_correct else "option"
                    processed_answer = process_html_content(opt['answer'])
                    html += f"<div class='{class_name}'>{labels[opt_idx]}) {processed_answer}</div>"
            html += "</div>"
        
        html += "</div></div>"
    
    html += """
<div class='quote-footer'>🎯 "𝔼𝕩𝕔𝕖𝕝𝕝𝔼𝔫𝔠𝔢 𝐢𝐬 𝐧𝑜𝐭 𝐚 𝐬𝐤𝐢𝐥𝐥, 𝐢𝐭'𝐬 𝐚𝐧 𝐚𝐭𝐭𝐢𝐭𝐮𝐝𝐞"</div>
<div class='extracted-box'>🚀 Crafted with Excellence by 『𝗛ᴀʀsʜ』</div>
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
    """Generate HTML answer key table - Modern Premium theme"""
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
    
    .quote::before {{
        content: '📚';
        position: absolute;
        top: -10px;
        left: 20px;
        font-size: 24px;
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
</head>
<body>
<div class='title-box'>
    <h1>{test_title}</h1>
    <div>🎯 Answer Key & Solutions</div>
</div>
<div class='quote'>📚 "𝙎𝙪𝙘𝙘𝙚𝙨𝙨 𝙞𝙨 𝙬𝙝𝙚𝙧𝙚 𝙥𝙧𝙚𝙥𝙖𝙧𝙖𝙩𝙞𝙤𝙣 𝙢𝙚𝙚𝙩𝙨 𝙤𝙥𝙥𝙤𝙧𝙩𝙪𝙣𝙞𝙩𝙮" ✨</div>

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
                correct_answer = process_html_content(opt['answer'])
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
<div class='quote-footer'>💡 "𝕂𝕟𝕠𝕨𝕝𝕖𝕕𝕘𝕖 𝐢𝐬 𝐩𝐨𝐰𝐞𝐫, 𝒶𝓅𝓅𝓁𝓎 𝒾𝓉 𝓌𝒾𝓈𝑒𝓁𝓎"</div>
<div class='extracted-box'>🌟 Masterfully Designed by 『𝗛ᴀʀsʜ』</div>
</body>
</html>"""
    return html

def generate_html_only_questions(data, test_title, syllabus):
    """Generate HTML with only questions (no answer highlighting) - Black theme"""
    return generate_html_with_answers(data, test_title, syllabus).replace(
        "class='option correct'", "class='option'"
    ).replace(
        "background: linear-gradient(135deg, #1a4d1a 0%, #2d5a2d 100%);",
        "background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);"
    )

def generate_answer_key_table(data, test_title, syllabus):
    """Generate HTML answer key table - Modern Premium Theme"""
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
        background: radial-gradient(circle at 30% 20%, #667eea 0%, #764ba2 25%, #1a0033 50%, #000000 100%);
        background-attachment: fixed;
        color: #f8fafc;
        padding: 32px;
        line-height: 1.7;
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
        background: url('data:image/svg+xml,<svg width="80" height="80" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd"><circle fill="%23ffffff" fill-opacity="0.03" cx="40" cy="40" r="2"/><circle fill="%23667eea" fill-opacity="0.02" cx="20" cy="60" r="1"/></g></svg>');
        z-index: -1;
        opacity: 0.6;
        animation: float 20s ease-in-out infinite;
    }}
    
    @keyframes float {{
        0%, 100% {{ transform: translateY(0px) rotate(0deg); }}
        50% {{ transform: translateY(-20px) rotate(180deg); }}
    }}
    
    .title-box {{
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.9) 0%, rgba(118, 75, 162, 0.9) 50%, rgba(240, 147, 251, 0.8) 100%);
        backdrop-filter: blur(25px);
        padding: 40px 32px;
        border-radius: 24px;
        text-align: center;
        margin-bottom: 40px;
        box-shadow: 
            0 25px 50px rgba(102, 126, 234, 0.4),
            0 0 0 1px rgba(255, 255, 255, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.25);
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
        background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.15), transparent);
        animation: shine 4s infinite;
    }}
    
    .title-box::after {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, transparent 50%, rgba(255, 255, 255, 0.05) 100%);
        border-radius: 24px;
        pointer-events: none;
    }}
    
    @keyframes shine {{
        0% {{ transform: translateX(-100%) translateY(-100%) rotate(45deg); }}
        100% {{ transform: translateX(100%) translateY(100%) rotate(45deg); }}
    }}
    
    .title-box h1 {{
        position: relative;
        z-index: 2;
        font-size: 36px;
        font-weight: 700;
        background: linear-gradient(135deg, #ffffff 0%, #f0f9ff 50%, #e0e7ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 8px 0;
        text-shadow: 0 2px 10px rgba(255, 255, 255, 0.3);
    }}
    
    .subtitle {{
        position: relative;
        z-index: 2;
        font-size: 18px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.9);
        margin: 0;
    }}
    
    .answer-key-container {{
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
        backdrop-filter: blur(25px);
        border-radius: 20px;
        padding: 32px;
        box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.4),
            0 0 0 1px rgba(255, 255, 255, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(148, 163, 184, 0.2);
        position: relative;
        overflow: hidden;
    }}
    
    .answer-key-container::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #667eea 75%, #764ba2 100%);
        background-size: 200% 100%;
        animation: gradient-slide 3s ease-in-out infinite;
    }}
    
    @keyframes gradient-slide {{
        0%, 100% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
    }}
    
    .answer-key-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0 16px;
        margin-top: 24px;
    }}
    
    .table-header {{
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.8) 0%, rgba(118, 75, 162, 0.8) 100%);
        backdrop-filter: blur(10px);
        color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }}
    
    .table-header th {{
        padding: 20px 24px;
        text-align: center;
        font-weight: 600;
        font-size: 16px;
        border: none;
        position: relative;
    }}
    
    .table-header th:first-child {{ border-radius: 12px 0 0 12px; }}
    .table-header th:last-child {{ border-radius: 0 12px 12px 0; }}
    
    .answer-row {{
        background: linear-gradient(135deg, rgba(51, 65, 85, 0.6) 0%, rgba(30, 41, 59, 0.8) 100%);
        backdrop-filter: blur(15px);
        border-radius: 12px;
        transition: all 0.4s ease;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(148, 163, 184, 0.1);
    }}
    
    .answer-row:hover {{
        transform: translateY(-4px) scale(1.01);
        background: linear-gradient(135deg, rgba(71, 85, 105, 0.8) 0%, rgba(51, 65, 85, 0.9) 100%);
        box-shadow: 0 12px 30px rgba(102, 126, 234, 0.2);
        border-color: rgba(102, 126, 234, 0.3);
    }}
    
    .answer-row td {{
        padding: 20px 24px;
        text-align: center;
        border: none;
        color: #e2e8f0;
        font-weight: 500;
        vertical-align: middle;
    }}
    
    .answer-row td:first-child {{ border-radius: 12px 0 0 12px; }}
    .answer-row td:last-child {{ border-radius: 0 12px 12px 0; }}
    
    .question-number {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #ffffff;
        padding: 10px 16px;
        border-radius: 10px;
        font-weight: 700;
        font-size: 16px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 50px;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    }}
    
    .correct-option {{
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: #ffffff;
        padding: 12px 18px;
        border-radius: 10px;
        font-weight: 700;
        font-size: 18px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 60px;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
        position: relative;
    }}
    
    .correct-option::before {{
        content: '✓';
        position: absolute;
        top: -5px;
        right: -5px;
        background: #34d399;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: bold;
    }}
    
    .answer-text {{
        text-align: left;
        color: #cbd5e1;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        padding: 16px 20px;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        font-weight: 500;
        line-height: 1.6;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }}
    
    .quote {{
        text-align: center;
        margin: 48px auto;
        padding: 32px 40px;
        background: linear-gradient(135deg, rgba(251, 191, 36, 0.15) 0%, rgba(245, 158, 11, 0.1) 100%);
        backdrop-filter: blur(25px);
        color: #fbbf24;
        border-radius: 20px;
        font-style: italic;
        font-size: 20px;
        font-weight: 600;
        box-shadow: 
            0 15px 35px rgba(251, 191, 36, 0.3),
            0 0 0 1px rgba(251, 191, 36, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(251, 191, 36, 0.4);
        max-width: 700px;
        position: relative;
        overflow: hidden;
    }}
    
    .quote::before {{
        content: '"';
        position: absolute;
        top: -20px;
        left: 30px;
        font-size: 100px;
        color: rgba(251, 191, 36, 0.2);
        font-family: serif;
        font-weight: bold;
    }}
    
    .quote::after {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.05), transparent);
        animation: shimmer 4s ease-in-out infinite;
    }}
    
    @keyframes shimmer {{
        0%, 100% {{ transform: translateX(-100%); }}
        50% {{ transform: translateX(100%); }}
    }}
    
    .quote-footer, .extracted-box {{
        text-align: center;
        margin: 32px auto;
        padding: 20px 32px;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(109, 40, 217, 0.15) 100%);
        backdrop-filter: blur(25px);
        color: #c4b5fd;
        border-radius: 16px;
        font-weight: 600;
        font-size: 16px;
        box-shadow: 
            0 12px 25px rgba(139, 92, 246, 0.3),
            0 0 0 1px rgba(139, 92, 246, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(139, 92, 246, 0.4);
        max-width: fit-content;
        position: relative;
    }}
    
    .extracted-box {{
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.15) 100%);
        color: #6ee7b7;
        border-color: rgba(16, 185, 129, 0.4);
        box-shadow: 
            0 12px 25px rgba(16, 185, 129, 0.3),
            0 0 0 1px rgba(16, 185, 129, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }}
    
    @media print {{
        body {{ 
            background: #000 !important; 
            -webkit-print-color-adjust: exact;
        }}
    }}
    
    @media (max-width: 768px) {{
        body {{ padding: 20px; }}
        .title-box {{ padding: 32px 24px; }}
        .title-box h1 {{ font-size: 28px; }}
        .answer-key-container {{ padding: 24px; }}
        .answer-key-table {{ border-spacing: 0 12px; }}
        .answer-row td {{ padding: 16px 20px; }}
        .quote {{ padding: 24px 28px; font-size: 18px; }}
    }}
</style>
</head>
<body>
<div class='title-box'>
    <h1>{test_title}</h1>
    <div class='subtitle'>✨ Premium Answer Key ✨</div>
</div>

<div class='quote'>🌟 "𝙏𝙝𝙚 𝙤𝙣𝙡𝙮 𝙞𝙢𝙥𝙤𝙨𝙨𝙞𝙗𝙡𝙚 𝙟𝙤𝙪𝙧𝙣𝙚𝙮 𝙞𝙨 𝙩𝙝𝙚 𝙤𝙣𝙚 𝙮𝙤𝙪 𝙣𝙚𝙫𝙚𝙧 𝙗𝙚𝙜𝙞𝙣" ✨</div>

<div class='answer-key-container'>
    <table class='answer-key-table'>
        <thead>
            <tr class='table-header'>
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
                correct_answer = process_html_content(opt['answer'])
                break
        
        html += f"""
            <tr class='answer-row'>
                <td><span class='question-number'>{idx}</span></td>
                <td><span class='correct-option'>{correct_option}</span></td>
                <td><div class='answer-text'>{correct_answer}</div></td>
            </tr>"""
    
    html += """
        </tbody>
    </table>
</div>

<div class='quote-footer'>🎯 "𝔼𝕩𝔠𝔢𝕝𝕝𝔢𝕟𝔠𝔢 𝐢𝐬 𝐧𝑜𝐭 𝐚 𝐬𝐤𝐢𝐥𝐥, 𝐢𝐭'𝐬 𝐚𝐧 𝐚𝐭𝐭𝐢𝐭𝐮𝐝𝐞"</div>
<div class='extracted-box'>🚀 Crafted with Excellence by 『𝗛ᴀʀsʜ』</div>
</body>
</html>"""
    return html
