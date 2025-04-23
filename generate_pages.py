import os
import re
from bs4 import BeautifulSoup

# 基準となる配色（変数名 -> 新しい色）
# generate_pages.py 内では直接使わないが、参照用に残す
TARGET_COLORS_REF = {
    "--color-1": "var(--primary-1)",
    "--color-2": "var(--primary-2)",
    "--color-3": "var(--bg-medium)",
    "--color-4": "var(--accent)",
    "--color-5": "var(--accent-red)",
    "--text-main": "var(--text-dark)",
    "--text-heading": "var(--primary-1)",
    "--text-sub": "var(--text-muted)",
    "--bg-light": "var(--bg-light)",
    "--bg-medium": "var(--bg-medium)",
}

# 直接指定されている色コードや古い変数を新しい変数に置換するルール
COLOR_REPLACEMENT_RULES = {
    # 古い色コード/変数 -> 新しい変数
    "rgba(242, 198, 61, 0.3)": "rgba(var(--rgb-primary-1), 0.1)",
    "rgba(242, 198, 61, 0.2)": "rgba(var(--rgb-primary-1), 0.05)",
    "rgba(242, 230, 61, 0.1)": "rgba(var(--rgb-primary-1), 0.05)",
    "var(--color-3)": "var(--bg-medium)",
    "rgba(242, 92, 5, 0.2)": "rgba(var(--rgb-primary-2), 0.1)",
    "var(--color-4)": "var(--accent)",
    "var(--color-5)": "var(--primary-1)",
    "#593C47": "var(--primary-1)",
    "#F2E63D": "var(--accent)",
    "#F2C53D": "var(--bg-medium)",
    "#F25C05": "var(--accent)",
    "#F24405": "var(--primary-1)",
    "#334155": "var(--text-dark)",
    "#1e40af": "var(--primary-1)",
    "#475569": "var(--text-muted)",
}

# template.htmlに追加した新しい:root定義と同じもの
BASE_CSS_VARIABLES = """
:root {
    --primary-1: #2B6CB0;
    --primary-2: #6B46C1;
    --accent: #4299E1;
    --accent-red: #E53E3E;
    --bg-light: #F7FAFC;
    --bg-medium: #E2E8F0;
    --text-dark: #1A202C;
    --text-muted: #4A5568;
    --rgb-primary-1: 43, 108, 176;
    --rgb-primary-2: 107, 70, 193;
}
"""

def read_template():
    with open('infographics/template.html', 'r', encoding='utf-8') as f:
        return f.read()

def read_content(content_file):
    with open(content_file, 'r', encoding='utf-8') as f:
        return f.read()

def extract_title(soup):
    title_tag = soup.find('title')
    if title_tag:
        return title_tag.get_text().strip()
    h1_tag = soup.find('h1') # コンテンツ内の最初のh1をタイトルとする
    if h1_tag:
        return h1_tag.get_text().strip()
    return "インフォグラフィック"

def extract_body_content(soup):
    # コンテンツの主要コンテナを探す (例: body直下のdiv.container)
    container = soup.select_one('body > div.container') 
    if container:
        return str(container)
    # 見つからない場合はbodyの中身全体を返す (headなどは除く)
    body_tag = soup.find('body')
    if body_tag:
        return ''.join(str(child) for child in body_tag.children)
    return ""

def update_css_colors(content_html):
    """コンテンツHTMLからCSSを抽出し、配色を置換してCSS文字列を返す"""
    soup = BeautifulSoup(content_html, 'html.parser')
    style_tag = soup.find('style')
    css_content = ""

    if style_tag and style_tag.string:
        css_content = style_tag.string
        
        # 1. 古い:root定義を削除 (存在する場合)
        css_content = re.sub(r":root\s*{[^}]*}\s*", "", css_content, flags=re.DOTALL)
        
        # 2. 古い変数参照と直接の色指定を置換
        sorted_rules = sorted(COLOR_REPLACEMENT_RULES.items(), key=lambda item: len(item[0]), reverse=True)
        for old_color, new_variable in sorted_rules:
            escaped_old_color = re.escape(old_color)
            css_content = css_content.replace(old_color, new_variable)
            
        # 3. 記事タイトルスタイルを強制的に修正
        #    .header-title セレクタを見つけて修正 (より複雑なセレクタも考慮可能)
        #    単純な文字列置換で試みる (CSSパーサーを使う方が確実だが複雑になる)
        title_style_pattern = re.compile(r"(\.header-title\s*\{)([^}]*)(\})", re.DOTALL)
        match = title_style_pattern.search(css_content)
        if match:
            existing_styles = match.group(2)
            # 不要なスタイル (background, background-clip, etc.) を削除
            existing_styles = re.sub(r"background[^;]*;", "", existing_styles)
            existing_styles = re.sub(r"-webkit-background-clip[^;]*;", "", existing_styles)
            existing_styles = re.sub(r"background-clip[^;]*;", "", existing_styles)
            existing_styles = re.sub(r"-webkit-text-fill-color[^;]*;", "", existing_styles)
            # color プロパティを上書き (すでにあれば置換、なければ追加)
            if "color:" in existing_styles:
                 existing_styles = re.sub(r"color\s*:[^;]*;", "color: var(--text-dark);", existing_styles)
            else:
                 existing_styles += " color: var(--text-dark);"
            # font-family も基本に合わせる (任意)
            # existing_styles = re.sub(r"font-family\s*:[^;]*;", "font-family: \"Noto Sans JP\", sans-serif;", existing_styles)
            
            # 更新したスタイルでCSS全体を再構築
            css_content = title_style_pattern.sub(r"\1" + existing_styles + r"\3", css_content)
        else:
            # .header-title のルールが見つからない場合、基本的な h1 にスタイルを適用するフォールバック (任意)
            # css_content += "\n.content h1 { color: var(--text-dark); }" # テンプレート側で指定済みのはず
            pass
            
    # BASE_CSS_VARIABLES はテンプレート側で定義されるので、ここでは含めない
    return css_content

def generate_page(content_file):
    template = read_template()
    content_html = read_content(content_file)
    
    content_soup = BeautifulSoup(content_html, 'html.parser')
    
    # タイトルを抽出
    title = extract_title(content_soup)
    
    # 本文コンテンツを抽出
    body_html_string = extract_body_content(content_soup)
    
    # コンテンツ固有CSSの配色を更新
    modified_css_string = update_css_colors(content_html)
    
    # テンプレートのプレースホルダーを置換
    page = template.replace('{%TITLE%}', title)
    page = page.replace('{%CONTENT_STYLES%}', modified_css_string)
    page = page.replace('{%CONTENT%}', body_html_string)
    
    # 出力ファイル名を生成
    output_file = os.path.basename(content_file)
    output_path = os.path.join('infographics', output_file)
    
    # 更新されたページ全体を保存
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(page) # prettifyは不要
    
    print(f'Generated: {output_file}')

def main():
    contents_dir = 'infographics/contents'
    output_dir = 'infographics'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    for file in os.listdir(contents_dir):
        if file.endswith('.html'):
            content_file = os.path.join(contents_dir, file)
            generate_page(content_file)

if __name__ == '__main__':
    main() 