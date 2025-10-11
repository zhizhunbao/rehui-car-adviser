import React from 'react';
import './ProgressIndicator.css';

interface ProgressStep {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'completed' | 'error';
  description?: string;
}

interface ProgressIndicatorProps {
  steps: ProgressStep[];
  currentStep?: string;
  className?: string;
  showDescription?: boolean;
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  steps,
  currentStep,
  className = '',
  showDescription = true
}) => {
  const getStepIcon = (step: ProgressStep) => {
    switch (step.status) {
      case 'completed':
        return '✓';
      case 'active':
        return '⟳';
      case 'error':
        return '✗';
      default:
        return '○';
    }
  };

  const getStepClass = (step: ProgressStep) => {
    return `progress-step ${step.status}`;
  };

  return (
    <div className={`progress-indicator ${className}`}>
      <div className="progress-track">
        {steps.map((step, index) => (
          <div key={step.id} className="step-container">
            <div className={getStepClass(step)}>
              <div className="step-icon">
                {getStepIcon(step)}
              </div>
              <div className="step-content">
                <div className="step-label">{step.label}</div>
                {showDescription && step.description && (
                  <div className="step-description">
                    {step.description}
                  </div>
                )}
              </div>
            </div>
            
            {/* 连接线 */}
            {index < steps.length - 1 && (
              <div className={`step-connector ${
                step.status === 'completed' ? 'completed' : ''
              }`} />
            )}
          </div>
        ))}
      </div>
      
      {/* 进度条 */}
      <div className="progress-bar">
        <div 
          className="progress-fill"
          style={{
            width: `${(steps.filter(s => s.status === 'completed').length / steps.length) * 100}%`
          }}
        />
      </div>
    </div>
  );
};

export default ProgressIndicator;
