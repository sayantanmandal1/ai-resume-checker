import React from 'react';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

import { 
  Zap, 
  Award, 
  TrendingUp, 
  Users, 
  Target, 
  User, 
  Mail, 
  CheckCircle, 
  XCircle, 
  Star, 
  Eye, 
  Download 
} from 'lucide-react';

const ResultsPage = ({ results, resetForm, selectedCandidate, setSelectedCandidate }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'Excellent Match': return 'text-green-600 bg-green-100';
      case 'Good Match': return 'text-blue-600 bg-blue-100';
      case 'Needs Improvement': return 'text-yellow-600 bg-yellow-100';
      case 'Poor Match': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };


const downloadReport = (candidate) => {
  const doc = new jsPDF();

  // Title
  doc.setFontSize(20);
  doc.setFont(undefined, 'bold');
  doc.text('Candidate Analysis Report', 14, 22);

  doc.setFontSize(12);
  doc.setFont(undefined, 'normal');

  let y = 35;
  const lineHeight = 8;

  doc.text(`Name: ${candidate.candidate_name || candidate.filename}`, 14, y);
  y += lineHeight;
  doc.text(`Email: ${candidate.candidate_email || 'N/A'}`, 14, y);
  y += lineHeight;
  doc.text(`Suggested Role: ${candidate.suggested_job_role || 'N/A'}`, 14, y);
  y += lineHeight;
  doc.text(`Score: ${candidate.score_out_of_100}%`, 14, y);
  y += lineHeight;
  doc.text(`Status: ${candidate.status}`, 14, y);
  y += lineHeight + 6;

  // Summary header
  doc.setFont(undefined, 'bold');
  doc.text('Summary:', 14, y);
  y += 6;

  // Summary text wrapped
  doc.setFont(undefined, 'normal');
  const splitSummary = doc.splitTextToSize(candidate.resume_summary || 'No summary provided.', 180);
  doc.text(splitSummary, 14, y);
  y += splitSummary.length * 6 + 8;

  // Skill scores table
  autoTable(doc, {
    startY: y,
    head: [['Category', 'Score']],
    body: [
      ['Skill Match', `${candidate.skill_match_score?.toFixed(1) || '0'}%`],
      ['Experience', `${candidate.experience_score?.toFixed(1) || '0'}%`],
    ],
    theme: 'striped',
    headStyles: { fillColor: [41, 128, 185], textColor: 255, fontStyle: 'bold' },
    margin: { left: 14, right: 14 },
  });

  const finalY = doc.previousAutoTable ? doc.previousAutoTable.finalY + 10 : y + 30;

  // Matching Skills
  doc.setFont(undefined, 'bold');
  doc.setFontSize(12);
  doc.text('Matching Skills:', 14, finalY);

  doc.setFont(undefined, 'normal');
  doc.setFontSize(10);

  if (candidate.matching_skills && candidate.matching_skills.length > 0) {
    candidate.matching_skills.forEach((skill, idx) => {
      doc.text(`• ${skill}`, 20, finalY + 8 + idx * 6);
    });
  } else {
    doc.text('None', 20, finalY + 8);
  }

  // Calculate y position after matching skills
  const afterMatchingSkillsY = finalY + 8 + ((candidate.matching_skills?.length || 1) * 6) + 10;

  // Missing Skills
  doc.setFont(undefined, 'bold');
  doc.setFontSize(12);
  doc.text('Missing Skills:', 14, afterMatchingSkillsY);

  doc.setFont(undefined, 'normal');
  doc.setFontSize(10);

  if (candidate.missing_skills && candidate.missing_skills.length > 0) {
    candidate.missing_skills.forEach((skill, idx) => {
      doc.text(`• ${skill}`, 20, afterMatchingSkillsY + 8 + idx * 6);
    });
  } else {
    doc.text('None', 20, afterMatchingSkillsY + 8);
  }

  doc.save(`${candidate.candidate_name || 'candidate'}_report.pdf`);
};

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-blue-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (!results) {
    return (
      <div className="results-section">
        <div className="no-results">
          <h2>No Results Available</h2>
          <p>Please upload resumes and run analysis first.</p>
          <button onClick={() => window.location.href = '/upload'} className="submit-btn">
            Go to Upload
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="results-section">
      <div className="results-header">
        <div>
          <h2>Analysis Results</h2>
          <p>Found {results.reports?.length || 0} candidates • {results.interview_invitations_sent || 0} interview invitations sent</p>
        </div>
        <button onClick={resetForm} className="reset-btn">
          <Zap size={18} />
          Reset Everything
        </button>
      </div>

      {/* Summary Stats */}
      <div className="summary-stats">
        <div className="stat-card">
          <div className="stat-icon excellent">
            <Award size={24} />
          </div>
          <div className="stat-content">
            <h3>{results.reports?.filter(r => r.status === 'Excellent Match').length || 0}</h3>
            <p>Excellent Matches</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon good">
            <TrendingUp size={24} />
          </div>
          <div className="stat-content">
            <h3>{results.reports?.filter(r => r.status === 'Good Match').length || 0}</h3>
            <p>Good Matches</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon interviews">
            <Users size={24} />
          </div>
          <div className="stat-content">
            <h3>{results.interview_invitations_sent || 0}</h3>
            <p>Interviews Sent</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon threshold">
            <Target size={24} />
          </div>
          <div className="stat-content">
            <h3>{results.suitability_threshold || 75}%</h3>
            <p>Threshold</p>
          </div>
        </div>
      </div>

      {/* Candidate List */}
      <div className="candidates-grid">
        {results.reports?.map((candidate, index) => (
          <div key={index} className="candidate-card">
            <div className="candidate-header">
              <div className="candidate-info">
                <div className="candidate-avatar">
                  <User size={24} />
                </div>
                <div>
                  <h3>{candidate.candidate_name || candidate.filename}</h3>
                  <p className="candidate-role">{candidate.suggested_job_role}</p>
                </div>
              </div>
              <div className={`score-badge ${getScoreColor(candidate.score_out_of_100)}`}>
                {candidate.score_out_of_100}%
              </div>
            </div>

            <div className="candidate-body">
              <div className={`status-badge ${getStatusColor(candidate.status)}`}>
                {candidate.status}
              </div>

              {candidate.candidate_email && (
                <div className="candidate-contact">
                  <Mail size={16} />
                  <span>{candidate.candidate_email}</span>
                </div>
              )}

              <div className="candidate-summary">
                <p>{candidate.resume_summary}</p>
              </div>

              <div className="score-breakdown">
                <div className="score-item">
                  <span className="score-label">Skill Match</span>
                  <div className="score-bar">
                    <div 
                      className="score-fill skill"
                      style={{ width: `${candidate.skill_match_score}%` }}
                    />
                  </div>
                  <span className="score-value">{candidate.skill_match_score?.toFixed(1)}%</span>
                </div>
                <div className="score-item">
                  <span className="score-label">Experience</span>
                  <div className="score-bar">
                    <div 
                      className="score-fill experience"
                      style={{ width: `${candidate.experience_score}%` }}
                    />
                  </div>
                  <span className="score-value">{candidate.experience_score?.toFixed(1)}%</span>
                </div>
              </div>

              <div className="skills-section">
                <div className="skills-group">
                  <h4 className="skills-title matching">
                    <CheckCircle size={16} />
                    Matching Skills ({candidate.matching_skills?.length || 0})
                  </h4>
                  <div className="skills-list">
                    {candidate.matching_skills?.slice(0, 6).map((skill, i) => (
                      <span key={i} className="skill-tag matching">{skill}</span>
                    ))}
                    {candidate.matching_skills?.length > 6 && (
                      <span className="skill-tag more">+{candidate.matching_skills.length - 6} more</span>
                    )}
                  </div>
                </div>

                {candidate.missing_skills?.length > 0 && (
                  <div className="skills-group">
                    <h4 className="skills-title missing">
                      <XCircle size={16} />
                      Missing Skills ({candidate.missing_skills.length})
                    </h4>
                    <div className="skills-list">
                      {candidate.missing_skills.slice(0, 4).map((skill, i) => (
                        <span key={i} className="skill-tag missing">{skill}</span>
                      ))}
                      {candidate.missing_skills.length > 4 && (
                        <span className="skill-tag more">+{candidate.missing_skills.length - 4} more</span>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {candidate.interview_eligible && (
                <div className="interview-status">
                  <div className="interview-badge">
                    <Star size={16} />
                    Interview Eligible
                  </div>
                  {candidate.email_sent && (
                    <div className="email-status">
                      <CheckCircle size={14} />
                      <span>Invitation Sent</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="candidate-actions">
                <button 
                    onClick={() => setSelectedCandidate(candidate)}
                    className="action-btn view"
                >
                    <Eye size={16} />
                    View Details
                </button>
                <button
                    className="action-btn download"
                    onClick={() => downloadReport(candidate)}
                    >
                    <Download size={16} />
                        Download Report
                </button>
            </div>
          </div>
        ))}
      </div>

      {/* Candidate Detail Modal */}
      {selectedCandidate && (
        <div className="modal-overlay" onClick={() => setSelectedCandidate(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedCandidate.candidate_name || selectedCandidate.filename}</h2>
              <button 
                onClick={() => setSelectedCandidate(null)}
                className="modal-close"
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="candidate-details">
                <div className="detail-section">
                  <h3>Summary</h3>
                  <p>{selectedCandidate.resume_summary}</p>
                </div>
                
                <div className="detail-section">
                  <h3>All Skills ({selectedCandidate.skills_present?.length || 0})</h3>
                  <div className="skills-list">
                    {selectedCandidate.skills_present?.map((skill, i) => (
                      <span key={i} className="skill-tag">{skill}</span>
                    ))}
                  </div>
                </div>

                {selectedCandidate.interview_credentials && (
                  <div className="detail-section">
                    <h3>Interview Credentials</h3>
                    <div className="credentials">
                      <p><strong>Username:</strong> {selectedCandidate.interview_credentials.username}</p>
                      <p><strong>Password:</strong> {selectedCandidate.interview_credentials.password}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultsPage;