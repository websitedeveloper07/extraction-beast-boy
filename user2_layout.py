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


# === HTML Generators ===
def generate_html_with_answers(data, test_title, syllabus):
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<title>{test_title}</title>
<style>
    body {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #121212;
        color: #e0e0e0;
        padding: 30px;
        line-height: 1.8;
    }}
    .title-box {{
        background: linear-gradient(to right, #8e2de2, #4a00e0);
        color: #ffffff;
        padding: 25px;
        border-radius: 14px;
        text-align: center;
        font-size: 28px;
        font-weight: 800;
        margin-bottom: 30px;
        box-shadow: 0 8px 25px rgba(138, 43, 226, 0.4);
        text-transform: uppercase;
        letter-spacing: 1.2px;
    }}
    .quote {{
        text-align: center;
        background: #2c2c2c;
        color: #ffcc80;
        font-style: italic;
        font-size: 17px;
        font-weight: 600;
        padding: 18px 22px;
        margin: 20px auto;
        max-width: 800px;
        border-radius: 12px;
        border-left: 6px solid #ff7043;
        box-shadow: 0 4px 16px rgba(255, 112, 67, 0.15);
    }}
    .question {{
        background: #1e1e1e;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 30px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        position: relative;
    }}
    .watermark {{
        position: absolute;
        top: 12px;
        right: 16px;
        background: #212121;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        font-family: monospace;
        color: #90caf9;
    }}
    .watermark a {{
        color: #90caf9;
        text-decoration: none;
    }}
    .watermark a:hover {{
        text-decoration: underline;
        color: #bbdefb;
    }}
    .question h3 {{
        color: #64b5f6;
        font-size: 21px;
        margin-bottom: 14px;
    }}
    .question-body {{
        margin-bottom: 18px;
    }}
    .options {{
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
    }}
    .option {{
        flex: 1 1 calc(50% - 10px);
        background: #2a2a2a;
        border-left: 4px solid #616161;
        padding: 14px 18px;
        border-radius: 8px;
        transition: all 0.3s ease;
        word-wrap: break-word;
        font-weight: 500;
    }}
    .option.correct {{
        background: #1b5e20;
        border-left-color: #66bb6a;
        color: #c8e6c9;
        font-weight: 600;
        box-shadow: 0 0 10px rgba(102, 187, 106, 0.3);
    }}
    .quote-footer {{
        text-align: center;
        margin-top: 40px;
        padding: 16px 24px;
        font-style: italic;
        background: linear-gradient(to right, #3f51b5, #1a237e);
        color: #ffffff;
        border-radius: 12px;
        font-size: 16px;
        font-weight: 600;
        box-shadow: 0 4px 20px rgba(63, 81, 181, 0.3);
        max-width: fit-content;
        margin-left: auto;
        margin-right: auto;
    }}
    .extracted-box {{
        margin-top: 20px;
        text-align: center;
        background: linear-gradient(to right, #26c6da, #00acc1);
        padding: 14px 20px;
        border-radius: 12px;
        font-size: 15px;
        font-weight: bold;
        color: #e0f7fa;
        box-shadow: 0 3px 10px rgba(0, 188, 212, 0.3);
    }}
</style>
</head>
<body>
<div class='title-box'>{test_title}</div>
<div class='quote'>“Don’t limit your challenges. Challenge your limits.”</div>
"""
    for idx, q in enumerate(data, 1):
        processed_body = process_html_content(q['body'])
        html += f"<div class='question'><div class='watermark'><a href='https://t.me/RockyLeakss' target='_blank'>@Hая$н</a></div>"
        html += f"<h3>Question {idx}</h3><div class='question-body'>{processed_body}</div><div class='options'>"

        alternatives = q['alternatives'][:4]
        labels = ['A', 'B', 'C', 'D']
        for i, opt in enumerate(alternatives):
            label = labels[i]
            is_correct = str(opt.get("score_if_chosen")) == "1"
            css_class = "option correct" if is_correct else "option"
            processed = process_html_content(opt['answer'])
            html += f"<div class='{css_class}'>{label}) {processed}</div>"

        html += "</div></div>"

    html += "<div class='quote-footer'>𝕋𝕙𝕖 𝕆𝕟𝕖 𝕒𝕟𝕕 𝕆𝕟𝕝𝕪 ℙ𝕚𝕖𝕔𝕖</div>"
    html += "<div class='extracted-box'>Extracted by Harsh</div>\n</body>\n</html>"
    return html


def generate_html_only_questions(data, test_title, syllabus):
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<title>{test_title}</title>
<style>
    body {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #f4faff;
        color: #1c1c1c;
        padding: 30px;
        line-height: 1.8;
    }}
    .title-box {{
        background: linear-gradient(to right, #00c6ff, #0072ff);
        color: white;
        padding: 25px;
        border-radius: 14px;
        text-align: center;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 30px;
        box-shadow: 0 4px 14px rgba(0, 114, 255, 0.3);
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }}
    .quote {{
        text-align: center;
        background: #ffe0b2;
        color: #5d4037;
        font-style: italic;
        font-size: 17px;
        font-weight: 600;
        padding: 18px 22px;
        margin: 20px auto;
        max-width: 800px;
        border-radius: 12px;
        border-left: 6px solid #ff7043;
        box-shadow: 0 3px 10px rgba(255, 112, 67, 0.2);
    }}
    .question {{
        background: #ffffff;
        border: 1px solid #dce3ed;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 30px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
        position: relative;
    }}
    .watermark {{
        position: absolute;
        top: 12px;
        right: 16px;
        background: #e3f2fd;
        color: #0277bd;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        font-family: monospace;
    }}
    .question h3 {{
        color: #01579b;
        font-size: 20px;
        margin-bottom: 14px;
    }}
    .question-body {{
        margin-bottom: 18px;
    }}
    .options {{
        display: flex;
        flex-direction: column;
        gap: 14px;
    }}
    .option {{
        padding: 14px 18px;
        border-radius: 8px;
        background: #f0f4f8;
        border-left: 5px solid #90a4ae;
    }}
    .quote-footer {{
        text-align: center;
        margin-top: 35px;
        padding: 14px 20px;
        font-style: italic;
        background: #dcedc8;
        color: #33691e;
        border-radius: 12px;
        font-size: 16px;
        font-weight: 600;
        max-width: fit-content;
        margin-left: auto;
        margin-right: auto;
    }}
    .extracted-box {{
        margin-top: 20px;
        text-align: center;
        background: linear-gradient(to right, #a7ffeb, #64ffda);
        padding: 14px 20px;
        border-radius: 12px;
        font-size: 15px;
        font-weight: bold;
        color: #00695c;
        box-shadow: 0 3px 10px rgba(0, 150, 136, 0.2);
    }}
</style>
</head>
<body>
<div class='title-box'>{test_title}</div>
<div class='quote'>“Don’t limit your challenges. Challenge your limits.”</div>
"""
    for idx, q in enumerate(data, 1):
        processed_body = process_html_content(q['body'])
        html += f"<div class='question'><div class='watermark'>@Harsh</div>"
        html += f"<h3>Question {idx}</h3><div class='question-body'>{processed_body}</div><div class='options'>"

        alternatives = q['alternatives'][:4]
        labels = ['A', 'B', 'C', 'D']
        for i, opt in enumerate(alternatives):
            label = labels[i]
            processed = process_html_content(opt['answer'])
            html += f"<div class='option'>{label}) {processed}</div>"

        html += "</div></div>"

    html += "<div class='quote-footer'>𝕋𝕙𝕖 𝕆𝕟𝕖 𝕒𝕟𝕕 𝕆𝕟𝕝𝕪 ℙ𝕚𝕖𝕔𝕖</div>"
    html += "<div class='extracted-box'>Extracted by Harsh</div>"
    html += "</body></html>"
    return html


def generate_answer_key_table(data, test_title, syllabus):
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<title>{test_title} - Answer Key</title>
<style>
    body {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #f4faff;
        color: #1c1c1c;
        padding: 30px;
        line-height: 1.8;
    }}
    .title-box {{
        background: linear-gradient(to right, #00c6ff, #0072ff);
        color: white;
        padding: 25px;
        border-radius: 14px;
        text-align: center;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 30px;
        box-shadow: 0 4px 14px rgba(0, 114, 255, 0.3);
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }}
    .quote {{
        text-align: center;
        background: #ffe0b2;
        color: #5d4037;
        font-style: italic;
        font-size: 17px;
        font-weight: 600;
        padding: 18px 22px;
        margin: 20px auto;
        max-width: 800px;
        border-radius: 12px;
        border-left: 6px solid #ff7043;
        box-shadow: 0 3px 10px rgba(255, 112, 67, 0.2);
    }}
    .answer-key-container {{
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.05);
        margin-bottom: 30px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }}
    th, td {{
        padding: 14px;
        border: 1px solid #e0e0e0;
        text-align: center;
        font-size: 15px;
    }}
    th {{
        background-color: #0072ff;
        color: white;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    tr:nth-child(even) {{
        background-color: #f0f4f8;
    }}
    .question-number {{
        font-weight: 600;
        color: #1565c0;
    }}
    .correct-option {{
        background: #42a5f5;
        color: white;
        padding: 6px 10px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
        display: inline-block;
    }}
    .answer-text {{
        text-align: left;
        font-size: 14px;
        color: #37474f;
    }}
    .quote-footer {{
        text-align: center;
        margin-top: 35px;
        padding: 14px 20px;
        font-style: italic;
        background: #dcedc8;
        color: #33691e;
        border-radius: 12px;
        font-size: 16px;
        font-weight: 600;
        max-width: fit-content;
        margin-left: auto;
        margin-right: auto;
    }}
    .extracted-box {{
        margin-top: 20px;
        text-align: center;
        background: linear-gradient(to right, #a7ffeb, #64ffda);
        padding: 14px 20px;
        border-radius: 12px;
        font-size: 15px;
        font-weight: bold;
        color: #00695c;
        box-shadow: 0 3px 10px rgba(0, 150, 136, 0.2);
    }}
</style>
</head>
<body>
<div class='title-box'>{test_title}</div>
<div class='quote'>“Don’t limit your challenges. Challenge your limits.”</div>
<div class='answer-key-container'>
<table>
<thead>
<tr><th>Question No.</th><th>Correct Option</th><th>Answer Text</th></tr>
</thead>
<tbody>
"""
    for idx, q in enumerate(data, 1):
        correct_option = ""
        correct_answer = ""
        for i, opt in enumerate(q['alternatives'][:4]):
            if str(opt.get("score_if_chosen")) == "1":
                correct_option = ["A", "B", "C", "D"][i]
                correct_answer = process_html_content(opt['answer'])
                break
        html += f"""
<tr>
    <td class='question-number'>{idx}</td>
    <td><span class='correct-option'>{correct_option}</span></td>
    <td class='answer-text'>{correct_answer}</td>
</tr>
"""

    html += """
</tbody>
</table>
</div>
<div class='quote-footer'>Curated with precision by Harsh's Extractor</div>
<div class='extracted-box'>Extracted by Harsh</div>
</body>
</html>
"""
    return html
