import React from 'react';
import './Footer.css';

interface FooterProps {
  className?: string;
}

const Footer: React.FC<FooterProps> = ({ className = '' }) => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className={`footer ${className}`}>
      <div className="footer-content">
        <div className="footer-section">
          <h3 className="footer-title">热汇车源顾问</h3>
          <p className="footer-description">
            专业的车源咨询平台，为您提供最优质的购车建议和车源信息。
          </p>
        </div>
        
        <div className="footer-section">
          <h4 className="footer-subtitle">快速链接</h4>
          <ul className="footer-links">
            <li><a href="#about" className="footer-link">关于我们</a></li>
            <li><a href="#contact" className="footer-link">联系我们</a></li>
            <li><a href="#privacy" className="footer-link">隐私政策</a></li>
            <li><a href="#terms" className="footer-link">服务条款</a></li>
          </ul>
        </div>
        
        <div className="footer-section">
          <h4 className="footer-subtitle">服务支持</h4>
          <ul className="footer-links">
            <li><a href="#help" className="footer-link">帮助中心</a></li>
            <li><a href="#faq" className="footer-link">常见问题</a></li>
            <li><a href="#feedback" className="footer-link">意见反馈</a></li>
            <li><a href="#support" className="footer-link">技术支持</a></li>
          </ul>
        </div>
        
        <div className="footer-section">
          <h4 className="footer-subtitle">联系方式</h4>
          <div className="footer-contact">
            <p className="contact-item">
              <span className="contact-icon">📧</span>
              service@rehui.com
            </p>
            <p className="contact-item">
              <span className="contact-icon">📞</span>
              400-888-8888
            </p>
            <p className="contact-item">
              <span className="contact-icon">📍</span>
              北京市朝阳区
            </p>
          </div>
        </div>
      </div>
      
      <div className="footer-bottom">
        <div className="footer-bottom-content">
          <p className="footer-copyright">
            © {currentYear} 热汇车源顾问. 保留所有权利.
          </p>
          <div className="footer-social">
            <a href="#wechat" className="social-link" aria-label="微信">
              💬
            </a>
            <a href="#weibo" className="social-link" aria-label="微博">
              📱
            </a>
            <a href="#qq" className="social-link" aria-label="QQ">
              💬
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
