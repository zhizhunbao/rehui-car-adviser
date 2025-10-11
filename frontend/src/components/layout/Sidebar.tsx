import React from 'react';
import './Sidebar.css';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  currentView?: string;
  onViewChange?: (view: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  isOpen, 
  onClose, 
  currentView = 'conversation',
  onViewChange 
}) => {
  const menuItems = [
    { id: 'conversation', label: '对话咨询', icon: '💬' },
    { id: 'search', label: '车源搜索', icon: '🔍' },
    { id: 'favorites', label: '收藏车源', icon: '⭐' },
    { id: 'history', label: '历史记录', icon: '📋' },
    { id: 'settings', label: '设置', icon: '⚙️' }
  ];

  const handleItemClick = (itemId: string) => {
    onViewChange?.(itemId);
    onClose();
  };

  return (
    <>
      {/* 遮罩层 */}
      {isOpen && (
        <div 
          className="sidebar-overlay"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      
      {/* 侧边栏 */}
      <aside className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-header">
          <h2 className="sidebar-title">导航菜单</h2>
          <button 
            className="sidebar-close"
            onClick={onClose}
            aria-label="关闭菜单"
          >
            ✕
          </button>
        </div>
        
        <nav className="sidebar-nav">
          <ul className="sidebar-menu">
            {menuItems.map((item) => (
              <li key={item.id} className="sidebar-item">
                <button
                  className={`sidebar-link ${
                    currentView === item.id ? 'active' : ''
                  }`}
                  onClick={() => handleItemClick(item.id)}
                >
                  <span className="sidebar-icon">{item.icon}</span>
                  <span className="sidebar-label">{item.label}</span>
                </button>
              </li>
            ))}
          </ul>
        </nav>
        
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="user-avatar">👤</div>
            <div className="user-info">
              <div className="user-name">用户</div>
              <div className="user-status">在线</div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
