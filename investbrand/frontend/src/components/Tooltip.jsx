import React, { useState, useRef, useEffect } from 'react';
import { Info, X } from 'lucide-react';
import './Tooltip.css';

const Tooltip = ({ title, content, id, onLearnMore }) => {
  const [show, setShow] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setShow(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleGotIt = (e) => {
    e.stopPropagation();
    setShow(false);
    // Track dismiss locally
    if (id) {
       localStorage.setItem(`tooltip_dismissed_${id}`, 'true');
    }
  };

  // If dismissed forever, we might still show it on explicit hover/click but the PRD says:
  // "Can be dismissed but reappears on next session until user marks 'Got it'" 
  // For simplicity, we just use local state for showing/hiding when hovered/clicked.

  const handleLearnMore = (e) => {
    e.stopPropagation();
    if (onLearnMore) onLearnMore();
    setShow(false);
  };

  return (
    <div 
      className="tooltip-container"
      ref={containerRef}
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
      onClick={() => setShow(!show)}
    >
      <Info size={16} className="tooltip-icon" />
      {show && (
        <div className="tooltip-content">
          {title && <h4 className="tooltip-title">{title}</h4>}
          <p className="tooltip-text">{content}</p>
          <div className="tooltip-footer">
            {onLearnMore && (
              <button className="tooltip-learn-more" onClick={handleLearnMore}>Learn more &rarr;</button>
            )}
            <button className="tooltip-gotit" onClick={handleGotIt}>Got it</button>
          </div>
        </div>
      )}
    </div>
  );
};
export default Tooltip;
