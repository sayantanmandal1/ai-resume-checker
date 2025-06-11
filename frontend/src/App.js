import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';
import Header from './components/Header';
import UploadPage from './pages/UploadPage';
import ResultsPage from './pages/ResultsPage/ResultsPage';
import './App.css';

const AppContent = () => {
  const navigate = useNavigate();
  const [jobDescription, setJobDescription] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [selectedCandidate, setSelectedCandidate] = useState(null);

  const resetForm = () => {
    setJobDescription('');
    setSelectedFiles([]);
    setResults(null);
    setError('');
    setSelectedCandidate(null);
    navigate('/upload');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!jobDescription.trim()) {
      setError('Please enter a job description');
      setTimeout(() => setError(''), 3000);
      return;
    }
    
    if (selectedFiles.length === 0) {
      setError('Please upload at least one resume');
      setTimeout(() => setError(''), 3000);
      return;
    }

    setIsAnalyzing(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('job_description', jobDescription);
      selectedFiles.forEach(file => {
        formData.append('resume_pdfs', file);
      });

      const response = await fetch('http://127.0.0.1:8000/evaluate-resumes/', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
      // Navigate to results page after successful analysiss
      navigate('/results');
    } catch (err) {
      setError(`Analysis failed: ${err.message}`);
      setTimeout(() => setError(''), 5000);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="app">
      <Header />
      
      <main className="main-content">
        <div className="container">
          {/* Error Alert */}
          {error && (
            <div className="alert alert-error">
              <AlertCircle size={20} />
              <span>{error}</span>
            </div>
          )}

          <Routes>
            <Route 
              path="/upload" 
              element={
                <UploadPage 
                  jobDescription={jobDescription}
                  setJobDescription={setJobDescription}
                  selectedFiles={selectedFiles}
                  setSelectedFiles={setSelectedFiles}
                  isAnalyzing={isAnalyzing}
                  handleSubmit={handleSubmit}
                  setError={setError}
                />
              } 
            />
            <Route 
              path="/results" 
              element={
                <ResultsPage 
                  results={results}
                  resetForm={resetForm}
                  selectedCandidate={selectedCandidate}
                  setSelectedCandidate={setSelectedCandidate}
                />
              } 
            />
            <Route path="/" element={<Navigate to="/upload" replace />} />
          </Routes>
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="container">
          <p>
            &copy; Made with <span style={{ color: 'red' }}>♥</span> by{' '}
            <a
              href="https://github.com/sayantanmandal1"
              target="_blank"
              rel="noopener noreferrer"
            >
              github.com/sayantanmandal1
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
};

const App = () => {
  return (
    <Router>
      <AppContent />
    </Router>
  );
};

export default App;