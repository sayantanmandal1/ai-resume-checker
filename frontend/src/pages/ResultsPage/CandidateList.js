import React from 'react';
import CandidateCard from './CandidateCard';

const CandidateList = ({ reports, setSelectedCandidate }) => (
  <div className="candidates-grid">
    {reports?.map((candidate, index) => (
      <CandidateCard
        key={candidate.id || candidate.filename || Math.random()}
        candidate={candidate}
        setSelectedCandidate={setSelectedCandidate}
      />
    ))}
  </div>
);

export default CandidateList;
