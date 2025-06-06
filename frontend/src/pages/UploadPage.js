import React, { useState, useRef, useCallback } from 'react';
import { Upload, FileText, Briefcase, Send, Trash2 } from 'lucide-react';

const UploadPage = ({ 
  jobDescription, 
  setJobDescription, 
  selectedFiles, 
  setSelectedFiles, 
  isAnalyzing, 
  handleSubmit, 
  setError 
}) => {
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFiles = Array.from(e.dataTransfer.files);
      const validFiles = droppedFiles.filter(file => 
        file.type === 'application/pdf' || 
        file.type === 'application/msword' ||
        file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      );
      
      if (validFiles.length > 0) {
        setSelectedFiles(prev => [...prev, ...validFiles]);
      } else {
        setError('Please upload only PDF, DOC, or DOCX files');
        setTimeout(() => setError(''), 3000);
      }
    }
  }, [setSelectedFiles, setError]);

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    const validFiles = files.filter(file => 
      file.type === 'application/pdf' || 
      file.type === 'application/msword' ||
      file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    );
    
    if (validFiles.length > 0) {
      setSelectedFiles(prev => [...prev, ...validFiles]);
    } else {
      setError('Please upload only PDF, DOC, or DOCX files');
      setTimeout(() => setError(''), 3000);
    }
  };

  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="upload-section">
      <div className="section-header">
        <h1>AI-Powered Resume Analysis</h1>
        <p>Upload resumes and job descriptions to get intelligent matching insights</p>
      </div>
      
      <form className="upload-form" onSubmit={handleSubmit}>
        {/* Job Description */}
        <div className="form-group">
          <label className="form-label">
            <Briefcase className="label-icon" />
            Job Description
          </label>
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the complete job description here including required skills, experience, and qualifications..."
            className="job-description-input"
            rows={8}
          />
        </div>

        {/* File Upload */}
        <div className="form-group">
          <label className="form-label">
            <FileText className="label-icon" />
            Resume Files
          </label>

          <div
            className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="upload-content">
              <div className="upload-icon">
                <Upload size={48} />
              </div>
              <div className="upload-text">
                <h3>Drop files here or click to upload</h3>
                <p>Supports PDF, DOC, and DOCX files</p>
              </div>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.doc,.docx"
              onChange={handleFileSelect}
              className="file-input"
            />
          </div>

          {/* Selected Files */}
          {selectedFiles.length > 0 && (
            <div className="selected-files">
              <h4>Selected Files ({selectedFiles.length})</h4>
              <div className="file-list">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="file-item">
                    <div className="file-info">
                      <FileText className="file-icon" />
                      <div>
                        <span className="file-name">{file.name}</span>
                        <span className="file-size">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </span>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeFile(index)}
                      className="remove-file-btn"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isAnalyzing || !jobDescription.trim() || selectedFiles.length === 0}
          className="submit-btn"
        >
          {isAnalyzing ? (
            <>
              <div className="spinner" />
              Analyzing Resumes...
            </>
          ) : (
            <>
              <Send size={20} />
              Analyze Resumes
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default UploadPage;