import React from 'react';
import './Header.css';

interface HeaderProps {
  title?: string;
  onMenuClick?: () => void;
}

const Header: React.FC<HeaderProps> = ({ 
  title = "热汇车源顾问", 
  onMenuClick 
}) => {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <button 
            className="menu-button"
            onClick={onMenuClick}
            aria-label="菜单"
          >
            <span className="menu-icon">☰</span>
          </button>
          <h1 className="header-title">{title}</h1>
        </div>
        
        <div className="header-right">
          <div className="header-actions">
            <button className="action-button" aria-label="设置">
              ⚙️
            </button>
            <button className="action-button" aria-label="帮助">
              ❓
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
