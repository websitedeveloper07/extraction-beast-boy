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
<div class='quote'>𝐈𝐟 𝐥𝐢𝐟𝐞 𝐢𝐬 𝐭𝐨𝐨 𝐬𝐢𝐦𝐩𝐥𝐞 𝐢𝐭’𝐬 𝐧𝐨𝐭 𝐰𝐨𝐫𝐭𝐡 𝐥𝐢𝐯𝐢𝐧𝐠✨</div>
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
    html += "<div class='quote-footer'>𝕋𝕙𝕖 𝕆𝕟𝕖 𝕒𝕟𝕕 𝕆𝕟𝕝𝕪 ℙ𝕚𝕖𝕔𝕖</div>"
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
<div class='quote'>𝐈𝐟 𝐥𝐢𝐟𝐞 𝐢𝐬 𝐭𝐨𝐨 𝐬𝐢𝐦𝐩𝐥𝐞 𝐢𝐭’𝐬 𝐧𝐨𝐭 𝐰𝐨𝐫𝐭𝐡 𝐥𝐢𝐯𝐢𝐧𝐠✨</div>



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
<div class='quote-footer'>𝕋𝕙𝕖 𝕆𝕟𝕖 𝕒𝕟𝕕 𝕆𝕟𝕝𝕪 ℙ𝕚𝕖𝕔𝕖</div>
<div class='extracted-box'>Extracted by 『𝗥ᴏᴄ𝗄𝑦』</div>
</body>
</html>
    """
    return html
