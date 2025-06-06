import React from 'react';

const CandidateDetailModal = ({ candidate, close }) => (
  <div className="modal-overlay" onClick={close}>
    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
      <div className="modal-header">
        <h2>{candidate.candidate_name || candidate.filename}</h2>
        <button onClick={close} className="modal-close">×</button>
      </div>
      <div className="modal-body">
        <div className="candidate-details">
          <div className="detail-section">
            <h3>Summary</h3>
            <p>{candidate.resume_summary}</p>
          </div>

          <div className="detail-section">
            <h3>All Skills ({candidate.skills_present?.length || 0})</h3>
            <div className="skills-list">
              {candidate.skills_present?.map((skill, i) => (
                <span key={i} className="skill-tag">{skill}</span>
              ))}
            </div>
          </div>

          {candidate.interview_credentials && (
            <div className="detail-section">
              <h3>Interview Credentials</h3>
              <div className="credentials">
                <p><strong>Username:</strong> {candidate.interview_credentials.username}</p>
                <p><strong>Password:</strong> {candidate.interview_credentials.password}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  </div>
);

export default CandidateDetailModal;
