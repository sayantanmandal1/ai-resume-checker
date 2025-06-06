import React, { useState, useRef, useCallback } from 'react';
import { Upload, FileText, Briefcase, Send, CheckCircle, XCircle, User, Mail, Trophy, Target, BookOpen, Zap, Users, Clock, Eye, Trash2, Download, AlertCircle, Star, TrendingUp, Award } from 'lucide-react';

const App = () => {
  const [jobDescription, setJobDescription] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [activeTab, setActiveTab] = useState('upload');
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [sendingEmails, setSendingEmails] = useState(new Set());
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
  }, []);

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

      const response = await fetch('https://ai-resume-checker-1-tsrs.onrender.com/evaluate-resumes/', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
      setActiveTab('results');
    } catch (err) {
      setError(`Analysis failed: ${err.message}`);
      setTimeout(() => setError(''), 5000);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSendInterview = async (candidate, candidateIndex) => {
    if (!candidate.candidate_email) {
      setError('No email address found for this candidate');
      setTimeout(() => setError(''), 3000);
      return;
    }

    setSendingEmails(prev => new Set([...prev, candidateIndex]));

    try {
      const response = await fetch('https://ai-resume-checker-1-tsrs.onrender.com/send-interview-invitation/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          candidate_email: candidate.candidate_email,
          candidate_name: candidate.candidate_name || candidate.filename,
          job_description: jobDescription,
          interview_credentials: candidate.interview_credentials
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to send email: ${response.status}`);
      }

      // Update the results to mark email as sent
      setResults(prev => ({
        ...prev,
        reports: prev.reports.map((report, index) => 
          index === candidateIndex 
            ? { ...report, email_sent: true }
            : report
        ),
        interview_invitations_sent: (prev.interview_invitations_sent || 0) + 1
      }));

    } catch (err) {
      setError(`Failed to send interview invitation: ${err.message}`);
      setTimeout(() => setError(''), 5000);
    } finally {
      setSendingEmails(prev => {
        const newSet = new Set(prev);
        newSet.delete(candidateIndex);
        return newSet;
      });
    }
  };

  const handleSendAllInterviews = async () => {
    const eligibleCandidates = results.reports?.filter(
      (candidate, index) => candidate.interview_eligible && !candidate.email_sent
    ) || [];

    if (eligibleCandidates.length === 0) {
      setError('No eligible candidates to send interviews to');
      setTimeout(() => setError(''), 3000);
      return;
    }

    for (let i = 0; i < results.reports.length; i++) {
      const candidate = results.reports[i];
      if (candidate.interview_eligible && !candidate.email_sent) {
        await handleSendInterview(candidate, i);
        // Add a small delay between emails to avoid overwhelming the server
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Excellent Match': return 'text-green-600 bg-green-100';
      case 'Good Match': return 'text-blue-600 bg-blue-100';
      case 'Needs Improvement': return 'text-yellow-600 bg-yellow-100';
      case 'Poor Match': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-blue-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const resetForm = () => {
    setJobDescription('');
    setSelectedFiles([]);
    setResults(null);
    setError('');
    setActiveTab('upload');
    setSelectedCandidate(null);
    setSendingEmails(new Set());
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#f8fafc',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      {/* Header */}
      <header style={{
        backgroundColor: 'white',
        borderBottom: '1px solid #e2e8f0',
        padding: '1rem 0'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Target size={32} style={{ color: '#3b82f6' }} />
              <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1e293b' }}>
                AI Resume Evaluator
              </span>
            </div>
            <nav style={{ display: 'flex', gap: '0.5rem' }}>
              <button 
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.75rem 1rem',
                  backgroundColor: activeTab === 'upload' ? '#3b82f6' : 'transparent',
                  color: activeTab === 'upload' ? 'white' : '#64748b',
                  border: '1px solid #e2e8f0',
                  borderRadius: '0.5rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onClick={() => setActiveTab('upload')}
              >
                <Upload size={18} />
                Upload & Analyze
              </button>
              <button 
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.75rem 1rem',
                  backgroundColor: activeTab === 'results' ? '#3b82f6' : 'transparent',
                  color: activeTab === 'results' ? 'white' : '#64748b',
                  border: '1px solid #e2e8f0',
                  borderRadius: '0.5rem',
                  cursor: results ? 'pointer' : 'not-allowed',
                  opacity: results ? 1 : 0.5,
                  transition: 'all 0.2s'
                }}
                onClick={() => setActiveTab('results')}
                disabled={!results}
              >
                <Trophy size={18} />
                Results
              </button>
            </nav>
          </div>
        </div>
      </header>

      <main style={{ padding: '2rem 0' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1rem' }}>
          {/* Error Alert */}
          {error && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              padding: '1rem',
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '0.5rem',
              color: '#dc2626',
              marginBottom: '1.5rem'
            }}>
              <AlertCircle size={20} />
              <span>{error}</span>
            </div>
          )}

          {/* Upload Tab */}
          {activeTab === 'upload' && (
            <div>
              <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <h1 style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#1e293b', marginBottom: '0.5rem' }}>
                  AI-Powered Resume Analysis
                </h1>
                <p style={{ fontSize: '1.125rem', color: '#64748b' }}>
                  Upload resumes and job descriptions to get intelligent matching insights
                </p>
              </div>

              <form onSubmit={handleSubmit} style={{ maxWidth: '800px', margin: '0 auto' }}>
                {/* Job Description */}
                <div style={{ marginBottom: '2rem' }}>
                  <label style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    fontSize: '1.125rem',
                    fontWeight: '600',
                    color: '#374151',
                    marginBottom: '0.75rem'
                  }}>
                    <Briefcase size={20} />
                    Job Description
                  </label>
                  <textarea
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    placeholder="Paste the complete job description here including required skills, experience, and qualifications..."
                    style={{
                      width: '100%',
                      minHeight: '200px',
                      padding: '1rem',
                      border: '2px solid #e2e8f0',
                      borderRadius: '0.75rem',
                      fontSize: '1rem',
                      resize: 'vertical',
                      outline: 'none',
                      transition: 'border-color 0.2s'
                    }}
                    rows={8}
                  />
                </div>

                {/* File Upload */}
                <div style={{ marginBottom: '2rem' }}>
                  <label style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    fontSize: '1.125rem',
                    fontWeight: '600',
                    color: '#374151',
                    marginBottom: '0.75rem'
                  }}>
                    <FileText size={20} />
                    Resume Files
                  </label>

                  <div
                    style={{
                      border: `2px dashed ${dragActive ? '#3b82f6' : '#cbd5e1'}`,
                      borderRadius: '0.75rem',
                      padding: '3rem 2rem',
                      textAlign: 'center',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      backgroundColor: dragActive ? '#eff6ff' : 'white'
                    }}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
                      <Upload size={48} style={{ color: '#64748b' }} />
                      <div>
                        <h3 style={{ fontSize: '1.25rem', fontWeight: '600', color: '#374151', marginBottom: '0.5rem' }}>
                          Drop files here or click to upload
                        </h3>
                        <p style={{ color: '#64748b' }}>Supports PDF, DOC, and DOCX files</p>
                      </div>
                    </div>

                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      accept=".pdf,.doc,.docx"
                      onChange={handleFileSelect}
                      style={{ display: 'none' }}
                    />
                  </div>

                  {/* Selected Files */}
                  {selectedFiles.length > 0 && (
                    <div style={{ marginTop: '1.5rem' }}>
                      <h4 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#374151', marginBottom: '1rem' }}>
                        Selected Files ({selectedFiles.length})
                      </h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        {selectedFiles.map((file, index) => (
                          <div key={index} style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            padding: '1rem',
                            backgroundColor: 'white',
                            border: '1px solid #e2e8f0',
                            borderRadius: '0.5rem'
                          }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                              <FileText size={20} style={{ color: '#64748b' }} />
                              <div>
                                <div style={{ fontWeight: '500', color: '#374151' }}>{file.name}</div>
                                <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
                                  {(file.size / 1024 / 1024).toFixed(2)} MB
                                </div>
                              </div>
                            </div>
                            <button
                              type="button"
                              onClick={() => removeFile(index)}
                              style={{
                                padding: '0.5rem',
                                backgroundColor: '#fef2f2',
                                border: '1px solid #fecaca',
                                borderRadius: '0.375rem',
                                color: '#dc2626',
                                cursor: 'pointer',
                                transition: 'all 0.2s'
                              }}
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
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.75rem',
                    width: '100%',
                    padding: '1rem 2rem',
                    backgroundColor: isAnalyzing || !jobDescription.trim() || selectedFiles.length === 0 ? '#94a3b8' : '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.75rem',
                    fontSize: '1.125rem',
                    fontWeight: '600',
                    cursor: isAnalyzing || !jobDescription.trim() || selectedFiles.length === 0 ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  {isAnalyzing ? (
                    <>
                      <div style={{
                        width: '20px',
                        height: '20px',
                        border: '2px solid #ffffff',
                        borderTop: '2px solid transparent',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                      }} />
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
          )}

          {/* Results Tab */}
          {activeTab === 'results' && results && (
            <div>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '2rem'
              }}>
                <div>
                  <h2 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1e293b', marginBottom: '0.5rem' }}>
                    Analysis Results
                  </h2>
                  <p style={{ color: '#64748b' }}>
                    Found {results.reports?.length || 0} candidates • {results.interview_invitations_sent || 0} interview invitations sent
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '0.75rem' }}>
                  <button 
                    onClick={handleSendAllInterviews}
                    disabled={!results.reports?.some(r => r.interview_eligible && !r.email_sent)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.75rem 1rem',
                      backgroundColor: results.reports?.some(r => r.interview_eligible && !r.email_sent) ? '#10b981' : '#94a3b8',
                      color: 'white',
                      border: 'none',
                      borderRadius: '0.5rem',
                      cursor: results.reports?.some(r => r.interview_eligible && !r.email_sent) ? 'pointer' : 'not-allowed',
                      transition: 'all 0.2s'
                    }}
                  >
                    <Mail size={18} />
                    Send All Interviews
                  </button>
                  <button 
                    onClick={resetForm}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.75rem 1rem',
                      backgroundColor: '#3b82f6',
                      color: 'white',
                      border: 'none',
                      borderRadius: '0.5rem',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                  >
                    <Zap size={18} />
                    New Analysis
                  </button>
                </div>
              </div>

              {/* Summary Stats */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '1.5rem',
                marginBottom: '2rem'
              }}>
                <div style={{
                  backgroundColor: 'white',
                  padding: '1.5rem',
                  borderRadius: '0.75rem',
                  border: '1px solid #e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem'
                }}>
                  <div style={{
                    width: '48px',
                    height: '48px',
                    backgroundColor: '#dcfce7',
                    borderRadius: '0.75rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <Award size={24} style={{ color: '#16a34a' }} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1e293b', marginBottom: '0.25rem' }}>
                      {results.reports?.filter(r => r.status === 'Excellent Match').length || 0}
                    </h3>
                    <p style={{ color: '#64748b' }}>Excellent Matches</p>
                  </div>
                </div>
                <div style={{
                  backgroundColor: 'white',
                  padding: '1.5rem',
                  borderRadius: '0.75rem',
                  border: '1px solid #e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem'
                }}>
                  <div style={{
                    width: '48px',
                    height: '48px',
                    backgroundColor: '#dbeafe',
                    borderRadius: '0.75rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <TrendingUp size={24} style={{ color: '#2563eb' }} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1e293b', marginBottom: '0.25rem' }}>
                      {results.reports?.filter(r => r.status === 'Good Match').length || 0}
                    </h3>
                    <p style={{ color: '#64748b' }}>Good Matches</p>
                  </div>
                </div>
                <div style={{
                  backgroundColor: 'white',
                  padding: '1.5rem',
                  borderRadius: '0.75rem',
                  border: '1px solid #e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem'
                }}>
                  <div style={{
                    width: '48px',
                    height: '48px',
                    backgroundColor: '#f3e8ff',
                    borderRadius: '0.75rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <Users size={24} style={{ color: '#9333ea' }} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1e293b', marginBottom: '0.25rem' }}>
                      {results.interview_invitations_sent || 0}
                    </h3>
                    <p style={{ color: '#64748b' }}>Interviews Sent</p>
                  </div>
                </div>
                <div style={{
                  backgroundColor: 'white',
                  padding: '1.5rem',
                  borderRadius: '0.75rem',
                  border: '1px solid #e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem'
                }}>
                  <div style={{
                    width: '48px',
                    height: '48px',
                    backgroundColor: '#fef3c7',
                    borderRadius: '0.75rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <Target size={24} style={{ color: '#d97706' }} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1e293b', marginBottom: '0.25rem' }}>
                      {results.suitability_threshold || 75}%
                    </h3>
                    <p style={{ color: '#64748b' }}>Threshold</p>
                  </div>
                </div>
              </div>

              {/* Candidate List */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
                gap: '1.5rem'
              }}>
                {results.reports?.map((candidate, index) => (
                  <div key={index} style={{
                    backgroundColor: 'white',
                    borderRadius: '0.75rem',
                    border: '1px solid #e2e8f0',
                    padding: '1.5rem',
                    boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
                  }}>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      marginBottom: '1rem'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{
                          width: '48px',
                          height: '48px',
                          backgroundColor: '#f1f5f9',
                          borderRadius: '0.75rem',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}>
                          <User size={24} style={{ color: '#64748b' }} />
                        </div>
                        <div>
                          <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#1e293b', marginBottom: '0.25rem' }}>
                            {candidate.candidate_name || candidate.filename}
                          </h3>
                          <p style={{ color: '#64748b', fontSize: '0.875rem' }}>
                            {candidate.suggested_job_role}
                          </p>
                        </div>
                      </div>
                      <div style={{
                        padding: '0.5rem 0.75rem',
                        borderRadius: '0.5rem',
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        color: getScoreColor(candidate.score_out_of_100).replace('text-', ''),
                        backgroundColor: getScoreColor(candidate.score_out_of_100).includes('green') ? '#dcfce7' : 
                                        getScoreColor(candidate.score_out_of_100).includes('blue') ? '#dbeafe' :
                                        getScoreColor(candidate.score_out_of_100).includes('yellow') ? '#fef3c7' : '#fef2f2'
                      }}>
                        {candidate.score_out_of_100}%
                      </div>
                    </div>

                    <div style={{
                      display: 'inline-block',
                      padding: '0.5rem 0.75rem',
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      marginBottom: '1rem',
                      ...getStatusColor(candidate.status).split(' ').reduce((acc, cls) => {
                        if (cls.startsWith('text-')) acc.color = `var(--${cls.replace('text-', '')})`;
                        if (cls.startsWith('bg-')) acc.backgroundColor = `var(--${cls.replace('bg-', '')})`;
                        return acc;
                      }, {
                        color: getStatusColor(candidate.status).includes('green') ? '#16a34a' : 
                               getStatusColor(candidate.status).includes('blue') ? '#2563eb' :
                               getStatusColor(candidate.status).includes('yellow') ? '#d97706' : '#dc2626',
                        backgroundColor: getStatusColor(candidate.status).includes('green') ? '#dcfce7' : 
                                        getStatusColor(candidate.status).includes('blue') ? '#dbeafe' :
                                        getStatusColor(candidate.status).includes('yellow') ? '#fef3c7' : '#fef2f2'
                      })
                    }}>
                      {candidate.status}
                    </div>

                    {candidate.candidate_email && (
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        color: '#64748b',
                        fontSize: '0.875rem',
                        marginBottom: '1rem'
                      }}>
                        <Mail size={16} />
                        <span>{candidate.candidate_email}</span>
                      </div>
                    )}

                    <div style={{ marginBottom: '1rem', color: '#374151', fontSize: '0.875rem', lineHeight: '1.5' }}>
                      {candidate.resume_summary}
                    </div>

                    {/* Score Breakdown */}
                    <div style={{ marginBottom: '1rem' }}>
                      <div style={{ marginBottom: '0.75rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                          <span style={{ fontSize: '0.875rem', color: '#64748b' }}>Skill Match</span>
                          <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#374151' }}>
                            {candidate.skill_match_score?.toFixed(1)}%
                          </span>
                        </div>
                        <div style={{
                          width: '100%',
                          height: '8px',
                          backgroundColor: '#f1f5f9',
                          borderRadius: '4px',
                          overflow: 'hidden'
                        }}>
                          <div style={{
                            width: `${candidate.skill_match_score}%`,
                            height: '100%',
                            backgroundColor: '#10b981',
                            borderRadius: '4px',
                            transition: 'width 0.3s ease'
                          }} />
                        </div>
                      </div>
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                          <span style={{ fontSize: '0.875rem', color: '#64748b' }}>Experience</span>
                          <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#374151' }}>
                            {candidate.experience_score?.toFixed(1)}%
                          </span>
                        </div>
                        <div style={{
                          width: '100%',
                          height: '8px',
                          backgroundColor: '#f1f5f9',
                          borderRadius: '4px',
                          overflow: 'hidden'
                        }}>
                          <div style={{
                            width: `${candidate.experience_score}%`,
                            height: '100%',
                            backgroundColor: '#3b82f6',
                            borderRadius: '4px',
                            transition: 'width 0.3s ease'
                          }} />
                        </div>
                      </div>
                    </div>

                    {/* Skills Section */}
                    <div style={{ marginBottom: '1rem' }}>
                      <div style={{ marginBottom: '0.75rem' }}>
                        <h4 style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                          fontSize: '0.875rem',
                          fontWeight: '600',
                          color: '#059669',
                          marginBottom: '0.5rem'
                        }}>
                          <CheckCircle size={16} />
                          Matching Skills ({candidate.matching_skills?.length || 0})
                        </h4>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                          {candidate.matching_skills?.slice(0, 6).map((skill, i) => (
                            <span key={i} style={{
                              padding: '0.25rem 0.5rem',
                              backgroundColor: '#dcfce7',
                              color: '#16a34a',
                              borderRadius: '0.375rem',
                              fontSize: '0.75rem',
                              fontWeight: '500'
                            }}>
                              {skill}
                            </span>
                          ))}
                          {candidate.matching_skills?.length > 6 && (
                            <span style={{
                              padding: '0.25rem 0.5rem',
                              backgroundColor: '#f1f5f9',
                              color: '#64748b',
                              borderRadius: '0.375rem',
                              fontSize: '0.75rem',
                              fontWeight: '500'
                            }}>
                              +{candidate.matching_skills.length - 6} more
                            </span>
                          )}
                        </div>
                      </div>

                      {candidate.missing_skills?.length > 0 && (
                        <div>
                          <h4 style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            fontSize: '0.875rem',
                            fontWeight: '600',
                            color: '#dc2626',
                            marginBottom: '0.5rem'
                          }}>
                            <XCircle size={16} />
                            Missing Skills ({candidate.missing_skills.length})
                          </h4>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                            {candidate.missing_skills.slice(0, 4).map((skill, i) => (
                              <span key={i} style={{
                                padding: '0.25rem 0.5rem',
                                backgroundColor: '#fef2f2',
                                color: '#dc2626',
                                borderRadius: '0.375rem',
                                fontSize: '0.75rem',
                                fontWeight: '500'
                              }}>
                                {skill}
                              </span>
                            ))}
                            {candidate.missing_skills.length > 4 && (
                              <span style={{
                                padding: '0.25rem 0.5rem',
                                backgroundColor: '#f1f5f9',
                                color: '#64748b',
                                borderRadius: '0.375rem',
                                fontSize: '0.75rem',
                                fontWeight: '500'
                              }}>
                                +{candidate.missing_skills.length - 4} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Interview Status */}
                    {candidate.interview_eligible && (
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0.75rem',
                        backgroundColor: '#eff6ff',
                        borderRadius: '0.5rem',
                        marginBottom: '1rem'
                      }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                          color: '#2563eb',
                          fontSize: '0.875rem',
                          fontWeight: '600'
                        }}>
                          <Star size={16} />
                          Interview Eligible
                        </div>
                        {candidate.email_sent && (
                          <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                            color: '#059669',
                            fontSize: '0.75rem'
                          }}>
                            <CheckCircle size={14} />
                            <span>Invitation Sent</span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Actions */}
                    <div style={{
                      display: 'flex',
                      gap: '0.75rem',
                      paddingTop: '1rem',
                      borderTop: '1px solid #e2e8f0'
                    }}>
                      <button 
                        onClick={() => setSelectedCandidate(candidate)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                          padding: '0.5rem 0.75rem',
                          backgroundColor: '#f8fafc',
                          border: '1px solid #e2e8f0',
                          borderRadius: '0.375rem',
                          color: '#475569',
                          cursor: 'pointer',
                          fontSize: '0.875rem',
                          transition: 'all 0.2s'
                        }}
                      >
                        <Eye size={16} />
                        View Details
                      </button>
                      
                      {candidate.interview_eligible && !candidate.email_sent && (
                        <button 
                          onClick={() => handleSendInterview(candidate, index)}
                          disabled={sendingEmails.has(index)}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            padding: '0.5rem 0.75rem',
                            backgroundColor: sendingEmails.has(index) ? '#94a3b8' : '#10b981',
                            border: 'none',
                            borderRadius: '0.375rem',
                            color: 'white',
                            cursor: sendingEmails.has(index) ? 'not-allowed' : 'pointer',
                            fontSize: '0.875rem',
                            fontWeight: '500',
                            transition: 'all 0.2s'
                          }}
                        >
                          {sendingEmails.has(index) ? (
                            <>
                              <div style={{
                                width: '16px',
                                height: '16px',
                                border: '2px solid #ffffff',
                                borderTop: '2px solid transparent',
                                borderRadius: '50%',
                                animation: 'spin 1s linear infinite'
                              }} />
                              Sending...
                            </>
                          ) : (
                            <>
                              <Mail size={16} />
                              Send Interview
                            </>
                          )}
                        </button>
                      )}
                      
                      <button style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        padding: '0.5rem 0.75rem',
                        backgroundColor: '#f8fafc',
                        border: '1px solid #e2e8f0',
                        borderRadius: '0.375rem',
                        color: '#475569',
                        cursor: 'pointer',
                        fontSize: '0.875rem',
                        transition: 'all 0.2s'
                      }}>
                        <Download size={16} />
                        Download Report
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Candidate Detail Modal */}
          {selectedCandidate && (
            <div style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000,
              padding: '1rem'
            }} onClick={() => setSelectedCandidate(null)}>
              <div style={{
                backgroundColor: 'white',
                borderRadius: '0.75rem',
                maxWidth: '600px',
                width: '100%',
                maxHeight: '80vh',
                overflow: 'auto'
              }} onClick={(e) => e.stopPropagation()}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '1.5rem',
                  borderBottom: '1px solid #e2e8f0'
                }}>
                  <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1e293b' }}>
                    {selectedCandidate.candidate_name || selectedCandidate.filename}
                  </h2>
                  <button 
                    onClick={() => setSelectedCandidate(null)}
                    style={{
                      width: '32px',
                      height: '32px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: '#f1f5f9',
                      border: 'none',
                      borderRadius: '0.5rem',
                      color: '#64748b',
                      cursor: 'pointer',
                      fontSize: '1.5rem',
                      fontWeight: 'bold'
                    }}
                  >
                    ×
                  </button>
                </div>
                <div style={{ padding: '1.5rem' }}>
                  <div style={{ marginBottom: '1.5rem' }}>
                    <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#374151', marginBottom: '0.75rem' }}>
                      Summary
                    </h3>
                    <p style={{ color: '#64748b', lineHeight: '1.6' }}>
                      {selectedCandidate.resume_summary}
                    </p>
                  </div>
                  
                  <div style={{ marginBottom: '1.5rem' }}>
                    <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#374151', marginBottom: '0.75rem' }}>
                      All Skills ({selectedCandidate.skills_present?.length || 0})
                    </h3>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {selectedCandidate.skills_present?.map((skill, i) => (
                        <span key={i} style={{
                          padding: '0.375rem 0.75rem',
                          backgroundColor: '#f1f5f9',
                          color: '#475569',
                          borderRadius: '0.375rem',
                          fontSize: '0.875rem',
                          fontWeight: '500'
                        }}>
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>

                  {selectedCandidate.interview_credentials && (
                    <div>
                      <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#374151', marginBottom: '0.75rem' }}>
                        Interview Credentials
                      </h3>
                      <div style={{
                        padding: '1rem',
                        backgroundColor: '#f8fafc',
                        borderRadius: '0.5rem',
                        border: '1px solid #e2e8f0'
                      }}>
                        <p style={{ marginBottom: '0.5rem', color: '#374151' }}>
                          <strong>Username:</strong> {selectedCandidate.interview_credentials.username}
                        </p>
                        <p style={{ color: '#374151' }}>
                          <strong>Password:</strong> {selectedCandidate.interview_credentials.password}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer style={{
        backgroundColor: 'white',
        borderTop: '1px solid #e2e8f0',
        padding: '2rem 0',
        textAlign: 'center'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1rem' }}>
          <p style={{ color: '#64748b' }}>
            &copy; Made with <span style={{ color: 'red' }}>♥</span> by{' '}
            <a
              href="https://github.com/sayantanmandal1"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#3b82f6', textDecoration: 'none' }}
            >
              github.com/sayantanmandal1
            </a>
          </p>
        </div>
      </footer>

      {/* Add spinning animation */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default App;