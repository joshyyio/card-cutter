# 🎯 LD Debate Card Cutter

A modern web application that transforms articles and PDFs into professionally formatted Lincoln-Douglas debate cards using AI.

## ✨ Features

- **Multiple Input Sources**: Accept article URLs or upload PDF files
- **AI-Powered Card Cutting**: Uses GPT-4 to intelligently select and format relevant content
- **Professional Formatting**: 
  - **Bold** for important sentences
  - _Underline_ for emphasis during reading
  - [HIGHLIGHT] for key impactful phrases
- **Export Options**: Copy to clipboard or download as PDF
- **Beautiful UI**: Modern, responsive design with smooth animations
- **Side Selection**: Customize cards for Affirmative or Negative positions

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+
- OpenAI API key

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the backend directory:
```
OPENAI_API_KEY=your_openai_api_key_here
```

5. Run the Flask server:
```bash
python app.py
```

The backend will start on `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The frontend will start on `http://localhost:3000`

## 📖 Usage

1. **Choose Input Source**: Select between URL or PDF upload
2. **Enter Source**: 
   - For URL: Paste the article URL
   - For PDF: Upload your PDF file
3. **Enter Topic**: Type the LD debate resolution (e.g., "RESOLVED: The United States ought to...")
4. **Select Side**: Choose Affirmative or Negative
5. **Cut Card**: Click the "✂️ Cut Card" button
6. **Export**: Copy the text or download as PDF

## 🛠️ Technology Stack

### Backend
- **Flask**: Python web framework
- **PyMuPDF**: PDF text extraction
- **newspaper3k**: Article extraction from URLs
- **OpenAI API**: GPT-4 for intelligent card cutting

### Frontend
- **React**: UI framework with TypeScript
- **Axios**: API communication
- **html2canvas & jsPDF**: PDF export functionality
- **CSS3**: Modern styling with animations

## 🎨 Architecture

```
cardcutter/
├── backend/
│   ├── app.py              # Flask application
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Environment variables
└── frontend/
    ├── src/
    │   ├── App.tsx        # Main React component
    │   ├── components/
    │   │   ├── InputForm.tsx    # Form for user inputs
    │   │   └── CardDisplay.tsx  # Card rendering & export
    │   └── *.css          # Styling files
    └── package.json       # Node dependencies
```

## 🔧 Configuration

### Environment Variables

Backend (`.env`):
- `OPENAI_API_KEY`: Your OpenAI API key

Frontend (optional):
- `REACT_APP_API_URL`: Backend URL (defaults to http://localhost:5000)

## 📝 API Endpoints

- `POST /api/cut-card`: Process article/PDF and generate debate card
  - Form data: `topic`, `side`, `url` or `pdf` file
  - Returns: `card_text` and `card_html`
- `GET /api/health`: Health check endpoint

## 🤝 Contributing

Feel free to open issues or submit pull requests for improvements!

## 📄 License

MIT License - feel free to use this for your debate prep! 