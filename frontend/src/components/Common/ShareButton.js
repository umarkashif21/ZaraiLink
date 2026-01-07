import React, { useState } from 'react';
import './ShareButton.css';

const ShareButton = ({ 
  url,
  title = 'Check out this company on ZaraiLink',
  className = '' 
}) => {
  const [copied, setCopied] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const shareUrl = url || window.location.href;

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      
      const textArea = document.createElement('textarea');
      textArea.value = shareUrl;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleShare = async (platform) => {
    const encodedUrl = encodeURIComponent(shareUrl);
    const encodedTitle = encodeURIComponent(title);
    
    const shareUrls = {
      whatsapp: `https://wa.me/?text=${encodedTitle}%20${encodedUrl}`,
      linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`,
      twitter: `https://twitter.com/intent/tweet?text=${encodedTitle}&url=${encodedUrl}`,
      email: `mailto:?subject=${encodedTitle}&body=${encodedUrl}`,
    };
    
    if (shareUrls[platform]) {
      window.open(shareUrls[platform], '_blank', 'width=600,height=400');
    }
    setIsOpen(false);
  };

  
  const handleNativeShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({ title, url: shareUrl });
      } catch (err) {
        
      }
    }
  };

  return (
    <div className={`share-button-container ${className}`}>
      <button
        className="share-button"
        onClick={() => navigator.share ? handleNativeShare() : setIsOpen(!isOpen)}
        aria-label="Share"
      >
        {/* <span className="share-icon">🔗</span> */}
        <span>Share</span>
      </button>
      
      {isOpen && !navigator.share && (
        <div className="share-dropdown">
          <button className="share-option" onClick={handleCopyLink}>
            <span>{copied ? 'Copied' : 'Copy'}</span>
            <span>{copied ? 'Copied!' : 'Copy Link'}</span>
          </button>
          <button className="share-option" onClick={() => handleShare('whatsapp')}>
            {/* <span>💬</span> */}
            <span>WhatsApp</span>
          </button>
          <button className="share-option" onClick={() => handleShare('linkedin')}>
            {/* <span>💼</span> */}
            <span>LinkedIn</span>
          </button>
          <button className="share-option" onClick={() => handleShare('twitter')}>
            {/* <span>🐦</span> */}
            <span>Twitter</span>
          </button>
          <button className="share-option" onClick={() => handleShare('email')}>
            {/* <span>📧</span> */}
            <span>Email</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default ShareButton;
