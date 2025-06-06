import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Upload, Trophy, Target } from 'lucide-react';

const Header = () => {
  const location = useLocation();
  const currentPath = location.pathname;

  return (
    <header className="app-header">
      <div className="container">
        <div className="header-content">
          <div className="logo">
            <Target className="logo-icon" />
            <span className="logo-text">AI Resume Evaluator</span>
          </div>
          <nav className="nav-tabs">
            <Link 
              to="/upload"
              className={`nav-tab ${currentPath === '/upload' ? 'active' : ''}`}
            >
              <Upload size={18} />
              Upload & Analyze
            </Link>
            <Link 
              to="/results"
              className={`nav-tab ${currentPath === '/results' ? 'active' : ''}`}
            >
              <Trophy size={18} />
              Results
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;