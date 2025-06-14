import os
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
import fitz  # PyMuPDF
from newspaper import Article
from openai import OpenAI
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, 
     origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"], 
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     send_wildcard=False)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin in ['http://localhost:3000', 'http://localhost:3001', 'http://127.0.0.1:3000']:
        response.headers.add('Access-Control-Allow-Origin', origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file using PyMuPDF"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_file.save(tmp_file.name)
            
            # Open PDF and extract text
            doc = fitz.open(tmp_file.name)
            text_content = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Clean up text and extract paragraphs
                paragraphs = [p.strip() for p in text.split('\n\n') if p.strip() and len(p.strip()) > 50]
                text_content.extend(paragraphs)
            
            doc.close()
            os.unlink(tmp_file.name)
            
        return '\n\n'.join(text_content)
    
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")

def extract_text_from_url(url):
    """Extract article text from URL using newspaper3k"""
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        # Get the article text
        text = article.text
        
        # Split into paragraphs and filter out short ones
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip() and len(p.strip()) > 50]
        
        return '\n\n'.join(paragraphs)
    
    except Exception as e:
        raise Exception(f"Error extracting article from URL: {str(e)}")

def cut_debate_card(source_text, topic, side, argument=""):
    """Send text to OpenAI API and get formatted debate card"""
    system_prompt = """You are an expert LD debate coach cutting cards for competitive debate. Your cards must be readable, flowing, and strategically highlighted.

CRITICAL REQUIREMENTS:
1. **COMPLETE SENTENCES ONLY** - Every sentence must be grammatically complete and flow naturally when read aloud
2. **MINIMAL HIGHLIGHTING** - Bold only 1-2 key words per sentence that prove your argument
3. **NATURAL FLOW** - The card should read like normal prose, not choppy fragments
4. **SELECTIVE CUTTING** - Only include the most relevant 2-3 sentences from the source
5. **CLEAR LOGIC** - Each sentence should build toward a clear conclusion

HIGHLIGHTING STRATEGY:
- Bold ONLY impact words: "causes," "leads to," "results in," "increases," "prevents," "solves"
- Bold ONLY outcome words: "war," "conflict," "peace," "stability," "collapse," "success"
- DO NOT bold descriptive words, adjectives, or connecting phrases
- Maximum 2 bolded phrases per sentence

GOOD EXAMPLE:
DEMOCRACY PREVENTS VIOLENT CONFLICT
Johnson 24 (Sarah Johnson, Professor of Political Science at Stanford, "Democratic Peace Theory Revisited," International Studies Quarterly, January 2024)

Democratic institutions **reduce the likelihood of war** because they provide peaceful channels for resolving disputes. When citizens can vote out leaders, governments face strong incentives to avoid costly conflicts that damage their electoral prospects. Historical evidence shows that established democracies **rarely engage in military conflicts** with other democratic states, creating zones of peace that promote regional stability.

NOTICE HOW THIS WORKS:
- Each sentence is complete and readable
- Only crucial impact words are bolded
- Flows naturally when read aloud  
- Clear logical progression
- No choppy fragments or over-highlighting

BAD EXAMPLE (DO NOT DO THIS):
**Democratic institutions** **reduce the likelihood** of **war** because they **provide peaceful channels** for **resolving disputes**. When **citizens** can **vote out leaders**, **governments** face **strong incentives** to **avoid costly conflicts**.

YOUR TASK: Find 2-3 of the strongest, most complete sentences from the source that support the argument. Bold only the most crucial 1-2 words per sentence. Make it flow naturally."""

    # Side-specific prompts
    side_instructions = {
        "affirmative": """
Focus on:
- Moral imperatives and obligations
- Solving harms/preventing catastrophe
- Benefits of affirming the resolution
- Positive impacts of action""",
        "negative": """
Focus on:
- Disadvantages and risks
- Unintended consequences
- Problems with the affirmative worldview
- Impacts of affirming/acting"""
    }

    # Build the user prompt with argument integration
    argument_instruction = ""
    if argument:
        argument_instruction = f"\nSPECIFIC ARGUMENT TO SUPPORT: {argument}\nFind evidence that directly proves this argument is true."
    
    user_prompt = f"""Topic: "{topic}"
Side: {side}
{side_instructions.get(side.lower(), "")}{argument_instruction}

Source text to cut from:
\"\"\"
{source_text}
\"\"\"

INSTRUCTIONS:
1. **READ THE ENTIRE SOURCE** - Find the 2-3 most powerful, complete sentences that support the {side} side
2. **SELECT STRATEGICALLY** - Choose sentences that create a clear logical chain
3. **PRESERVE SENTENCE INTEGRITY** - Use complete, grammatically correct sentences
4. **HIGHLIGHT MINIMALLY** - Bold only 1-2 crucial words per sentence (impact words like "causes," "prevents," "leads to," outcome words like "war," "peace," "collapse")
5. **ENSURE FLOW** - The card should read naturally when spoken aloud

The card should be concise (2-3 sentences), readable, and strategically highlighted to win rounds."""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,  # Balanced for faithful quoting with natural flow
            max_tokens=1500,     # Shorter limit to encourage conciseness
            presence_penalty=0.0,
            frequency_penalty=0.0
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        raise Exception(f"Error calling OpenAI API: {str(e)}")

def format_card_html(card_text):
    """Convert the card text to HTML with proper formatting"""
    # First, handle triple asterisks (most important)
    html = re.sub(r'\*\*\*(.*?)\*\*\*', r'<span class="triple-emphasis">\1</span>', card_text)
    
    # Then handle double asterisks
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong class="key-impact">\1</strong>', html)
    
    # Handle double underscores
    html = re.sub(r'__(.*?)__', r'<span class="important">\1</span>', html)
    
    # Handle single underscores (but not in URLs)
    # First, temporarily replace URLs to protect them
    url_pattern = r'https?://[^\s<>"\']+_[^\s<>"\']*'
    urls = re.findall(url_pattern, html)
    url_placeholders = {}
    for i, url in enumerate(urls):
        placeholder = f'__URL_PLACEHOLDER_{i}__'
        url_placeholders[placeholder] = url
        html = html.replace(url, placeholder)
    
    # Now safely apply underscore formatting
    html = re.sub(r'_([^_]+)_', r'<u>\1</u>', html)
    
    # Restore URLs
    for placeholder, url in url_placeholders.items():
        html = html.replace(placeholder, url)
    
    # Handle [HIGHLIGHT] tags
    html = re.sub(r'\[HIGHLIGHT\](.*?)\[/HIGHLIGHT\]', r'<span class="highlight">\1</span>', html)
    
    # Handle [...] for omitted text (discouraged but handle if present)
    html = re.sub(r'\[\.\.\.+\]', r'<span class="omitted">[...]</span>', html)
    
    # Handle [sic]
    html = re.sub(r'\[sic\]', r'<span class="sic">[sic]</span>', html)
    
    # Convert line breaks to <br> but preserve paragraph structure
    lines = html.split('\n')
    formatted_html = []
    
    for i, line in enumerate(lines):
        if line.strip():
            # Check if this is the tagline (first non-empty line, usually short)
            if i == 0 or (i == 1 and not lines[0].strip()):
                formatted_html.append(f'<h3 class="tagline">{line}</h3>')
            # Check if this is the citation (contains year pattern and parentheses)
            elif re.search(r"'\d{2}", line) and '(' in line and ')' in line:
                formatted_html.append(f'<p class="citation">{line}</p>')
            # Otherwise it's card text
            else:
                # Don't add extra line breaks within paragraphs
                if formatted_html and formatted_html[-1].startswith('<p class="card-text">'):
                    formatted_html[-1] = formatted_html[-1][:-4] + '<br>' + line + '</p>'
                else:
                    formatted_html.append(f'<p class="card-text">{line}</p>')
        elif formatted_html:  # Empty line creates paragraph break
            continue
    
    html = '\n'.join(formatted_html)
    
    # Wrap in container
    html = f'<div class="debate-card">\n{html}\n</div>'
    
    return html

@app.route('/api/cut-card', methods=['POST', 'OPTIONS'])
def cut_card():
    """Main endpoint for cutting debate cards"""
    # Handle preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    try:
        # Get form data
        topic = request.form.get('topic')
        side = request.form.get('side')
        argument = request.form.get('argument', '')
        url = request.form.get('url')
        
        # Validate inputs
        if not topic or not side:
            return jsonify({'error': 'Topic and side are required'}), 400
        
        # Extract text based on input type
        if 'pdf' in request.files:
            pdf_file = request.files['pdf']
            if pdf_file.filename == '':
                return jsonify({'error': 'No PDF file selected'}), 400
            source_text = extract_text_from_pdf(pdf_file)
        elif url:
            source_text = extract_text_from_url(url)
        else:
            return jsonify({'error': 'Either PDF or URL must be provided'}), 400
        
        # Cut the debate card
        card_text = cut_debate_card(source_text, topic, side, argument)
        
        # Format as HTML
        card_html = format_card_html(card_text)
        
        return jsonify({
            'success': True,
            'card_text': card_text,
            'card_html': card_html
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, port=5000) 