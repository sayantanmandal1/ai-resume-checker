import React from 'react';
import { Zap } from 'lucide-react';
import SummaryStats from './SummaryStats';
import CandidateList from './CandidateList';
import CandidateDetailModal from './CandidateDetailModal';

const ResultsPage = ({ results, resetForm, selectedCandidate, setSelectedCandidate }) => {
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

      <SummaryStats results={results} />
      <CandidateList
        reports={results.reports || []}
        setSelectedCandidate={setSelectedCandidate}
      />

      {selectedCandidate && (
        <CandidateDetailModal
          candidate={selectedCandidate}
          close={() => setSelectedCandidate(null)}
        />
      )}
    </div>
  );
};

export default ResultsPage;
