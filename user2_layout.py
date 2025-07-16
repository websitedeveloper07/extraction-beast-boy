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


# === HTML Generators - Black Theme ===
def generate_html_with_answers(data, test_title, syllabus):
    """Generate HTML with questions and highlighted correct answers - Black theme"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<title>{test_title}</title>
<style>
    body {{
        font-family: 'Segoe UI', Arial, sans-serif;
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
        color: #e0e0e0;
        padding: 20px;
        line-height: 1.6;
        margin: 0;
        min-height: 100vh;
    }}
    .title-box {{
        background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
        color: #00bfff;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 191, 255, 0.3);
        border: 2px solid #00bfff;
    }}
    .title-box h1 {{
        margin: 0;
        font-size: 26px;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(0, 191, 255, 0.5);
    }}
    .question-card {{
        position: relative;
        background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
        border: 1px solid #333;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
    }}
    .question-watermark {{
        position: absolute;
        top: 8px;
        right: 12px;
        background: rgba(0, 191, 255, 0.1);
        border: 1px solid #00bfff;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: bold;
        color: #00bfff;
        font-family: monospace;
    }}
    .question-watermark a {{
        color: #00bfff;
        text-decoration: none;
    }}
    .question-title {{
        font-size: 18px;
        font-weight: bold;
        color: #00bfff;
        margin-bottom: 10px;
    }}
    .question-body {{
        color: #d0d0d0;
        margin-bottom: 15px;
        white-space: pre-wrap;
        word-wrap: break-word;
    }}
    .options {{
        display: flex;
        flex-direction: column;
        gap: 8px;
    }}
    .option-row {{
        display: flex;
        gap: 8px;
    }}
    .option {{
        background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
        border: 1px solid #444;
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        color: #d0d0d0;
        width: 50%;
        box-sizing: border-box;
    }}
    .option.correct {{
        background: linear-gradient(135deg, #1a4d1a 0%, #2d5a2d 100%);
        border-color: #4caf50;
        color: #90ee90;
        box-shadow: 0 0 8px rgba(76, 175, 80, 0.3);
    }}
    .quote {{
        text-align: center;
        margin: 20px 0;
        padding: 16px;
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        color: #ffd700;
        border-radius: 10px;
        font-style: italic;
        font-size: 15px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.2);
        border: 1px solid #ffd700;
    }}
    .quote-footer, .extracted-box {{
        text-align: center;
        margin: 20px auto;
        padding: 12px 16px;
        background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
        color: #00bfff;
        border-radius: 10px;
        font-weight: bold;
        font-size: 14px;
        box-shadow: 0 4px 15px rgba(0, 191, 255, 0.2);
        border: 1px solid #00bfff;
        max-width: fit-content;
    }}
    @media print {{
        body {{ background: #000 !important; }}
        .question-card {{ page-break-inside: avoid; }}
    }}
</style>
</head>
<body>
<div class='title-box'>
    <h1>{test_title}</h1>
</div>
<div class='quote'>𝐈𝐟 𝐥𝐢𝐟𝐞 𝐢𝐬 𝐭𝐨𝐨 𝐬𝐢𝐦𝐩𝐥𝐞 𝐢𝐭'𝐬 𝐧𝐨𝐭 𝐰𝐨𝐫𝐭𝐡 𝐥𝐢𝐯𝐢𝐧𝐠✨</div>
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
<div class='quote-footer'>𝕋𝕙𝕖 𝕆𝕟𝕖 𝕒𝕟𝕕 𝕆𝕟𝕝𝕪 ℙ𝕚𝕖𝕔𝕖</div>
<div class='extracted-box'>Extracted by 『𝗛ᴀʀsʜ』</div>
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
    """Generate HTML answer key table - Black theme"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<title>{test_title} - Answer Key</title>
<style>
    body {{
        font-family: 'Segoe UI', Arial, sans-serif;
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
        color: #e0e0e0;
        padding: 20px;
        margin: 0;
        min-height: 100vh;
    }}
    .title-box {{
        background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
        color: #00bfff;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 191, 255, 0.3);
        border: 2px solid #00bfff;
    }}
    .title-box h1 {{
        margin: 0;
        font-size: 24px;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(0, 191, 255, 0.5);
    }}
    .answer-key-table {{
        width: 100%;
        border-collapse: collapse;
        background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
    }}
    .answer-key-table th {{
        background: linear-gradient(135deg, #333 0%, #1a1a1a 100%);
        color: #00bfff;
        padding: 12px;
        text-align: center;
        font-weight: bold;
        border-bottom: 2px solid #00bfff;
    }}
    .answer-key-table td {{
        padding: 10px;
        text-align: center;
        border-bottom: 1px solid #333;
        color: #d0d0d0;
    }}
    .answer-key-table tr:nth-child(even) {{
        background: rgba(255, 255, 255, 0.05);
    }}
    .answer-key-table tr:hover {{
        background: rgba(0, 191, 255, 0.1);
    }}
    .question-number {{
        background: linear-gradient(135deg, #00bfff 0%, #0080ff 100%);
        color: #000;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: bold;
    }}
    .correct-option {{
        background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
        color: #fff;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: bold;
    }}
    .answer-text {{
        text-align: left;
        color: #d0d0d0;
        background: rgba(0, 191, 255, 0.1);
        padding: 8px;
        border-radius: 6px;
        border-left: 3px solid #00bfff;
    }}
    .quote, .quote-footer, .extracted-box {{
        text-align: center;
        margin: 20px auto;
        padding: 16px;
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        color: #ffd700;
        border-radius: 10px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.2);
        border: 1px solid #ffd700;
        max-width: fit-content;
    }}
    .extracted-box {{ color: #00bfff; border-color: #00bfff; }}
</style>
</head>
<body>
<div class='title-box'>
    <h1>{test_title}</h1>
    <div>Answer Key</div>
</div>
<div class='quote'>𝐈𝐟 𝐥𝐢𝐟𝐞 𝐢𝐬 𝐭𝐨𝐨 𝐬𝐢𝐦𝐩𝐥𝐞 𝐢𝐭'𝐬 𝐧𝐨𝐭 𝐰𝐨𝐫𝐭𝐡 𝐥𝐢𝐯𝐢𝐧𝐠✨</div>

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
<div class='quote-footer'>𝕋𝕙𝕖 𝕆𝕟𝕖 𝕒𝕟𝕕 𝕆𝕟𝕝𝕪 ℙ𝕚𝕖𝕔𝕖</div>
<div class='extracted-box'>Extracted by 『𝗛ᴀʀsʜ』</div>
</body>
</html>"""
    return html
