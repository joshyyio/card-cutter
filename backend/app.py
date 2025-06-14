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

def cut_debate_card(source_text, topic, side):
    """Send text to OpenAI API and get formatted debate card"""
    system_prompt = """You are an expert debate coach cutting Lincoln-Douglas (LD) cards. 

CRITICAL FORMAT REQUIREMENTS:
1. TAGLINE: Start with a short, punchy tagline that summarizes the argument (5-10 words max)
2. CITATION: Author Last Name 'Year (Author full name, credentials if available, "Article Title", Publication, Date, URL if available)
3. CARD TEXT: The actual evidence formatted as follows:
   - - ***triple asterisks*** for the MOST critical phrases
   - **double asterisks** for important phrases
   - _single underscores_ for emphasis/terms to stress when reading
   - **[HIGHLIGHT]** around key impactful sections
   - *italics* for technical terms and key concepts
   - Use __double underscores__ for secondary important phrases
   - Keep full sentences and paragraphs for context
   - The card should flow naturally when read aloud

EXAMPLE FORMAT:
ECONOMIC COLLAPSE CAUSES NUCLEAR WAR
Smith '23 (John Smith, Professor of Economics at Harvard, "Global Economic Risks", Foreign Affairs, March 15, 2023)
Economic instability **directly increases the risk of nuclear conflict** between major powers. When nations face __severe economic pressure__, they become more likely to **pursue aggressive foreign policies** as a distraction from domestic troubles. History shows that __the Great Depression__ contributed to the rise of fascism and **ultimately led to World War II**.

IMPORTANT:
- Make cards punchy and impactful
- Prioritize evidence that directly links to the topic and side
- Cut for persuasion and clarity
- Keep the most impactful evidence"""

    user_prompt = f"""The LD topic is: "{topic}".
I am debating on the {side} side.

Here is the source text:
\"\"\"
{source_text}
\"\"\"

Please cut a card based on the arguments relevant to my side. Do NOT summarize—use real sentences and phrases from the article. Cut for maximum clarity and persuasiveness."""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        raise Exception(f"Error calling OpenAI API: {str(e)}")

def format_card_html(card_text):
    """Convert the card text to HTML with proper formatting"""
    # Replace **text** with <strong>text</strong>
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', card_text)
    
    # Replace _text_ with <u>text</u>
    html = re.sub(r'_(.*?)_', r'<u>\1</u>', html)
    
    # Replace [HIGHLIGHT]text[/HIGHLIGHT] or ALL CAPS with highlighted span
    html = re.sub(r'\[HIGHLIGHT\](.*?)\[/HIGHLIGHT\]', r'<span class="highlight">\1</span>', html)
    
    # Convert line breaks to <br>
    html = html.replace('\n', '<br>\n')
    
    # Wrap in paragraphs
    paragraphs = html.split('<br>\n<br>\n')
    html = '\n'.join([f'<p>{p}</p>' for p in paragraphs if p.strip()])
    
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
        card_text = cut_debate_card(source_text, topic, side)
        
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