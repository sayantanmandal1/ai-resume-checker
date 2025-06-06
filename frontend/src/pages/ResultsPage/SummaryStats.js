import React from 'react';
import { Award, TrendingUp, Users, Target } from 'lucide-react';

const SummaryStats = ({ results }) => (
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
);

export default SummaryStats;
