# 🎯 AI powered CV Evaluator

A modern, professional resume evaluation application that provides intelligent insights and scoring for resume-job matching using AI-powered analysis.

![CV Evaluator Demo](https://img.shields.io/badge/Status-Active-brightgreen)
![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

### 🎨 **Modern UI/UX**
- **Glassmorphism Design**: Beautiful frosted glass effects with backdrop blur
- **Custom Animations**: Smooth transitions, hover effects, and micro-interactions
- **Responsive Layout**: Optimized for desktop, tablet, and mobile devices
- **Professional Typography**: Clean, readable fonts with proper hierarchy
- **Interactive Elements**: Engaging hover states and visual feedback

### 🚀 **Core Functionality**
- **AI-Powered Analysis**: Intelligent resume evaluation against job descriptions
- **Drag & Drop Upload**: Seamless PDF file upload with visual feedback
- **Real-time Scoring**: Instant scoring out of 100 with status indicators
- **Job Role Suggestions**: AI-recommended job roles based on resume content
- **Similar Resume Matching**: Find similar resumes in the database

### 🔧 **Technical Features**
- **React-based**: Modern React application with hooks
- **Custom CSS**: Professional styling without external CSS frameworks
- **File Validation**: PDF-only uploads with error handling
- **Loading States**: Smooth loading animations and disabled states
- **Error Handling**: User-friendly error messages with animations

## 🏗️ Architecture

```
cv-evaluator/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── App.js           # Main application component
│   │   ├── index.js         # Entry point
│   │   └── styles/          # Custom CSS (embedded)
│   ├── public/
│   └── package.json
├── backend/                 # FastAPI backend (not included)
│   ├── main.py             # API endpoints
│   ├── models/             # AI models and processing
│   └── requirements.txt
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v14 or higher)
- **npm** or **yarn**
- **Python 3.8+** (for backend)
- **FastAPI backend** running on `http://localhost:8000`

### Frontend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/cv-evaluator.git
   cd cv-evaluator
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Start the development server**
   ```bash
   npm start
   # or
   yarn start
   ```

4. **Open your browser**
   ```
   http://localhost:3000
   ```

### Backend Setup (Required)

The frontend expects a FastAPI backend running on `http://localhost:8000`. The backend should provide:

```python
POST /evaluate-resume/
```

**Expected request format:**
- `Content-Type: multipart/form-data`
- `job_description`: Text field with job description
- `resume_pdf`: PDF file upload

**Expected response format:**
```json
{
  "score_out_of_100": 85,
  "status": "Excellent Match",
  "suggested_job_role": "Senior Software Engineer",
  "matched_resumes": [
    "Similar resume content excerpt...",
    "Another similar resume excerpt..."
  ]
}
```

## 📱 Usage

### 1. **Enter Job Description**
- Paste or type the job description in the text area
- The field supports multi-line input and is required

### 2. **Upload Resume**
- **Drag & Drop**: Simply drag a PDF file onto the upload area
- **Click to Browse**: Click the upload area to select a file
- **File Validation**: Only PDF files are accepted
- **Visual Feedback**: Upload area changes color when file is selected

### 3. **Evaluate Resume**
- Click the "Evaluate Resume" button
- Wait for AI analysis (loading state shown)
- View comprehensive results

### 4. **Review Results**
- **Match Score**: Numerical score out of 100
- **Status**: Qualitative assessment (Excellent, Good, Fair, etc.)
- **Suggested Role**: AI-recommended job position
- **Similar Resumes**: List of similar resumes from database

## 🎨 Design System

### **Color Palette**
- **Primary Gradient**: `#667eea` to `#764ba2`
- **Success**: `#10b981` (Green)
- **Warning**: `#f59e0b` (Amber)
- **Error**: `#ef4444` (Red)
- **Text**: `#1a202c` (Dark Gray)
- **Muted**: `#64748b` (Gray)

### **Typography**
- **Font Family**: Inter, system fonts
- **Headings**: 800 weight, gradient text
- **Body**: 400-600 weight
- **Code**: Monaco, Menlo, monospace

### **Animations**
- **Slide Up**: `cubic-bezier(0.175, 0.885, 0.32, 1.275)`
- **Fade In**: `ease-out` transitions
- **Hover Effects**: `cubic-bezier(0.4, 0, 0.2, 1)`
- **Loading Spinner**: Linear rotation

## 🔧 Configuration

### **API Endpoint**
Update the API endpoint in `App.js`:
```javascript
const response = await fetch("http://your-backend-url/evaluate-resume/", {
  method: "POST",
  body: formData,
});
```

### **File Upload Limits**
Modify file validation in the component:
```javascript
// Current: PDF only
accept="application/pdf"

// Add size validation
if (file.size > 10 * 1024 * 1024) { // 10MB limit
  setError("File size must be less than 10MB");
}
```

## 📊 Performance

### **Optimization Features**
- **Lazy Loading**: Components load only when needed
- **Efficient Re-renders**: Proper React state management
- **Lightweight**: No heavy external dependencies
- **Fast Animations**: Hardware-accelerated CSS transforms

### **Bundle Size**
- **Core App**: ~50KB (minified + gzipped)
- **Dependencies**: React, Lucide Icons only
- **Total**: ~150KB (including React)

## 🛠️ Development

### **Available Scripts**

```bash
# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test

# Eject configuration (not recommended)
npm run eject
```

### **Code Structure**

```javascript
// Main component structure
App.js
├── State Management (useState hooks)
├── Event Handlers (file upload, form submission)
├── API Integration (fetch requests)
├── UI Components (forms, results display)
└── Styling (embedded CSS)
```

### **Styling Approach**
- **No External CSS Frameworks**: Custom CSS for full control
- **CSS-in-JS Alternative**: Embedded styles in component
- **Modern CSS**: Flexbox, Grid, Custom Properties
- **Responsive Design**: Mobile-first approach

## 🔒 Security Considerations

### **File Upload Security**
- **File Type Validation**: Only PDF files accepted
- **Size Limits**: Prevent large file uploads
- **Client-side Validation**: First line of defense
- **Server-side Validation**: Required for security

### **API Security**
- **CORS Configuration**: Ensure proper CORS setup
- **Input Sanitization**: Validate all inputs server-side
- **Rate Limiting**: Prevent API abuse
- **Authentication**: Add user authentication if needed

## 🚀 Deployment
 Download the csv file from blob:https://github.com/e26e51cd-bd84-458a-88b3-f6f8c6bdaa92
### **Frontend Deployment**

#### **Netlify**
```bash
# Build the project
npm run build

# Deploy to Netlify
# Upload the build/ folder or connect your Git repository
```

#### **Vercel**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

#### **AWS S3 + CloudFront**
```bash
# Build the project
npm run build

# Upload to S3 bucket
aws s3 sync build/ s3://your-bucket-name

# Configure CloudFront distribution
```

### **Environment Variables**
Create `.env` file for environment-specific configuration:
```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_MAX_FILE_SIZE=10485760
REACT_APP_ENVIRONMENT=production
```

## 🧪 Testing

### **Testing Strategy**
- **Unit Tests**: Component-level testing
- **Integration Tests**: API integration testing
- **E2E Tests**: Full user workflow testing
- **Accessibility Tests**: WCAG compliance testing

### **Test Examples**
```javascript
// Component testing
test('renders CV Evaluator title', () => {
  render(<App />);
  expect(screen.getByText('CV Evaluator')).toBeInTheDocument();
});

// File upload testing
test('handles file upload', () => {
  render(<App />);
  const fileInput = screen.getByLabelText(/upload resume/i);
  const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
  fireEvent.change(fileInput, { target: { files: [file] } });
  expect(screen.getByText('test.pdf')).toBeInTheDocument();
});
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

### **Contribution Guidelines**
- Follow existing code style and conventions
- Add tests for new features
- Update documentation as needed
- Ensure responsive design compatibility
- Test across different browsers

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## 🙏 Acknowledgments

- **React Team**: For the amazing React framework
- **Lucide**: For beautiful, customizable icons
- **FastAPI**: For the robust backend framework
- **Claude AI**: For intelligent resume analysis capabilities

## 📞 Support

- **Documentation**: [Project Wiki](https://github.com/sayantanmandal1/cv-evaluator/wiki)
- **Issues**: [GitHub Issues](https://github.com/sayantanmandal1/cv-evaluator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sayantanmandal1/cv-evaluator/discussions)
- **Email**: msayantan05@gmail.com

## 🗺️ Roadmap

### **Version 1.1**
- [ ] User authentication and profiles
- [ ] Resume history and tracking
- [ ] Batch resume processing
- [ ] Advanced analytics dashboard

### **Version 1.2**
- [ ] Multiple file format support (DOCX, TXT)
- [ ] AI-powered resume improvement suggestions
- [ ] Integration with job boards
- [ ] Resume builder functionality

### **Version 2.0**
- [ ] Machine learning model improvements
- [ ] Real-time collaboration features
- [ ] Mobile app development
- [ ] Enterprise features and pricing

---

**Made with ❤️ by Sayantan**

*Last updated: May 2025*