import React, { useState } from "react";
import { Upload, FileText, CheckCircle, AlertCircle, Loader, Star, TrendingUp, Users } from "lucide-react";

function App() {
  const [jobDescription, setJobDescription] = useState("");
  const [resumeFile, setResumeFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFileChange = (e) => {
    setResumeFile(e.target.files[0]);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === "application/pdf") {
        setResumeFile(file);
      } else {
        setError("Please upload a PDF file only.");
      }
    }
  };

  const handleSubmit = async () => {
    setError(null);
    if (!jobDescription || !resumeFile) {
      setError("Please provide both job description and resume file.");
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("job_description", jobDescription);
      formData.append("resume_pdf", resumeFile);

      const response = await fetch("https://ai-resume-checker-1-tsrs.onrender.com/evaluate-resume/", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return "#10b981";
    if (score >= 60) return "#f59e0b";
    return "#ef4444";
  };

  const getStatusIcon = (status) => {
    if (status?.toLowerCase().includes("excellent") || status?.toLowerCase().includes("good")) {
      return <CheckCircle className="score-icon" />;
    }
    return <AlertCircle className="score-icon" />;
  };

  return (
    <>
      <style>{`
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        body {
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          min-height: 100vh;
          color: #1a202c;
        }

        .app-container {
          min-height: 100vh;
          padding: 2rem;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .main-card {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border-radius: 24px;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
          padding: 3rem;
          width: 100%;
          max-width: 800px;
          animation: slideUp 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275);
          border: 1px solid rgba(255, 255, 255, 0.2);
        }

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(50px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .header {
          text-align: center;
          margin-bottom: 3rem;
        }

        .title {
          font-size: 2.5rem;
          font-weight: 800;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          margin-bottom: 0.5rem;
          animation: fadeIn 1s ease-out 0.3s both;
        }

        .subtitle {
          color: #64748b;
          font-size: 1.1rem;
          animation: fadeIn 1s ease-out 0.5s both;
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .form-container {
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }

        .input-group {
          position: relative;
        }

        .label {
          display: block;
          font-weight: 600;
          color: #374151;
          margin-bottom: 0.75rem;
          font-size: 1rem;
        }

        .textarea {
          width: 100%;
          padding: 1rem;
          border: 2px solid #e5e7eb;
          border-radius: 12px;
          font-size: 1rem;
          font-family: inherit;
          resize: vertical;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          background: rgba(255, 255, 255, 0.8);
          backdrop-filter: blur(10px);
        }

        .textarea:focus {
          outline: none;
          border-color: #667eea;
          box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
          transform: translateY(-2px);
          background: rgba(255, 255, 255, 0.95);
        }

        .file-upload {
          position: relative;
          border: 2px dashed #d1d5db;
          border-radius: 12px;
          padding: 2rem;
          text-align: center;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          background: rgba(255, 255, 255, 0.5);
          backdrop-filter: blur(10px);
        }

        .file-upload:hover {
          border-color: #667eea;
          background: rgba(102, 126, 234, 0.05);
          transform: translateY(-2px);
        }

        .file-upload.drag-active {
          border-color: #667eea;
          background: rgba(102, 126, 234, 0.1);
          transform: scale(1.02);
        }

        .file-upload.has-file {
          border-color: #10b981;
          background: rgba(16, 185, 129, 0.05);
        }

        .upload-content {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1rem;
        }

        .upload-icon {
          width: 3rem;
          height: 3rem;
          color: #9ca3af;
          transition: all 0.3s ease;
        }

        .file-upload:hover .upload-icon {
          color: #667eea;
          transform: scale(1.1);
        }

        .upload-text {
          color: #6b7280;
          font-size: 1rem;
        }

        .file-name {
          color: #10b981;
          font-weight: 600;
          margin-top: 0.5rem;
        }

        .file-input {
          position: absolute;
          inset: 0;
          opacity: 0;
          cursor: pointer;
        }

        .submit-btn {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          padding: 1rem 2rem;
          border-radius: 12px;
          font-size: 1.1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
          position: relative;
          overflow: hidden;
        }

        .submit-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
        }

        .submit-btn:active:not(:disabled) {
          transform: translateY(0);
        }

        .submit-btn:disabled {
          opacity: 0.7;
          cursor: not-allowed;
          transform: none;
        }

        .btn-content {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
        }

        .loading-spinner {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .error-message {
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.2);
          border-radius: 12px;
          padding: 1rem;
          color: #dc2626;
          display: flex;
          align-items: center;
          gap: 0.5rem;
          animation: shake 0.5s ease-in-out;
        }

        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-5px); }
          75% { transform: translateX(5px); }
        }

        .result-card {
          background: rgba(255, 255, 255, 0.8);
          backdrop-filter: blur(20px);
          border-radius: 16px;
          padding: 2rem;
          margin-top: 2rem;
          border: 1px solid rgba(255, 255, 255, 0.2);
          animation: slideIn 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(30px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        .result-header {
          display: flex;
          align-items: center;
          gap: 1rem;
          margin-bottom: 2rem;
        }

        .result-title {
          font-size: 1.5rem;
          font-weight: 700;
          color: #1f2937;
        }

        .score-section {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
        }

        .score-card {
          background: rgba(255, 255, 255, 0.8);
          border-radius: 12px;
          padding: 1.5rem;
          text-align: center;
          border: 1px solid rgba(255, 255, 255, 0.3);
          transition: all 0.3s ease;
        }

        .score-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }

        .score-value {
          font-size: 2rem;
          font-weight: 800;
          margin-bottom: 0.5rem;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
        }

        .score-icon {
          width: 1.5rem;
          height: 1.5rem;
        }

        .score-label {
          color: #6b7280;
          font-weight: 500;
        }

        .similar-resumes {
          margin-top: 2rem;
        }

        .similar-title {
          font-size: 1.25rem;
          font-weight: 600;
          color: #1f2937;
          margin-bottom: 1rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .resume-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .resume-item {
          background: rgba(255, 255, 255, 0.6);
          border-radius: 8px;
          padding: 1rem;
          border-left: 4px solid #667eea;
          transition: all 0.3s ease;
          cursor: pointer;
        }

        .resume-item:hover {
          background: rgba(255, 255, 255, 0.8);
          transform: translateX(4px);
        }

        .resume-text {
          font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
          font-size: 0.875rem;
          line-height: 1.5;
          color: #4b5563;
          white-space: pre-wrap;
        }

        @media (max-width: 768px) {
          .app-container {
            padding: 1rem;
          }
          
          .main-card {
            padding: 2rem;
          }
          
          .title {
            font-size: 2rem;
          }
          
          .score-section {
            grid-template-columns: 1fr;
          }
        }
      `}</style>

      <div className="app-container">
        <div className="main-card">
          <div className="header">
            <h1 className="title">CV Evaluator</h1>
            <p className="subtitle">
              Get intelligent insights and scoring for resume-job matching
            </p>
          </div>

          <div className="form-container">
            <div className="input-group">
              <label className="label">
                <FileText style={{ width: '1.2rem', height: '1.2rem', display: 'inline', marginRight: '0.5rem' }} />
                Job Description
              </label>
              <textarea
                className="textarea"
                rows={4}
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the job description here..."
                required
              />
            </div>

            <div className="input-group">
              <label className="label">
                <Upload style={{ width: '1.2rem', height: '1.2rem', display: 'inline', marginRight: '0.5rem' }} />
                Resume Upload
              </label>
              <div
                className={`file-upload ${dragActive ? 'drag-active' : ''} ${resumeFile ? 'has-file' : ''}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={handleFileChange}
                  className="file-input"
                  required
                />
                <div className="upload-content">
                  <Upload className="upload-icon" />
                  <div className="upload-text">
                    {resumeFile ? (
                      <div className="file-name">
                        ✓ {resumeFile.name}
                      </div>
                    ) : (
                      <>
                        <div>Drop your PDF here or click to browse</div>
                        <div style={{ fontSize: '0.875rem', color: '#9ca3af' }}>
                          PDF files only, max 10MB
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <button type="button" onClick={handleSubmit} disabled={loading} className="submit-btn">
              <div className="btn-content">
                {loading ? (
                  <>
                    <Loader className="loading-spinner" style={{ width: '1.2rem', height: '1.2rem' }} />
                    Analyzing Resume...
                  </>
                ) : (
                  <>
                    <TrendingUp style={{ width: '1.2rem', height: '1.2rem' }} />
                    Evaluate Resume
                  </>
                )}
              </div>
            </button>
          </div>

          {error && (
            <div className="error-message">
              <AlertCircle style={{ width: '1.2rem', height: '1.2rem' }} />
              {error}
            </div>
          )}

          {result && (
            <div className="result-card">
              <div className="result-header">
                <Star style={{ width: '1.5rem', height: '1.5rem', color: '#f59e0b' }} />
                <h3 className="result-title">Evaluation Results</h3>
              </div>

              <div className="score-section">
                <div className="score-card">
                  <div className="score-value" style={{ color: getScoreColor(result.score_out_of_100) }}>
                    {result.score_out_of_100}
                    <span style={{ fontSize: '1rem', color: '#6b7280' }}>/100</span>
                  </div>
                  <div className="score-label">Match Score</div>
                </div>

                <div className="score-card">
                  <div className="score-value" style={{ color: getScoreColor(result.score_out_of_100) }}>
                    {getStatusIcon(result.status)}
                  </div>
                  <div className="score-label">{result.status}</div>
                </div>

                <div className="score-card">
                  <div className="score-value" style={{ color: '#667eea', fontSize: '1.2rem', fontWeight: '600' }}>
                    {result.suggested_job_role}
                  </div>
                  <div className="score-label">Suggested Role</div>
                </div>
              </div>

              {result.matched_resumes && result.matched_resumes.length > 0 && (
                <div className="similar-resumes">
                  <h4 className="similar-title">
                    <Users style={{ width: '1.2rem', height: '1.2rem' }} />
                    Similar Resumes ({result.matched_resumes.length})
                  </h4>
                  <div className="resume-list">
                    {result.matched_resumes.map((res, idx) => (
                      <div key={idx} className="resume-item">
                        <div className="resume-text">
                          {res.slice(0, 300)}
                          {res.length > 300 && '...'}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default App;