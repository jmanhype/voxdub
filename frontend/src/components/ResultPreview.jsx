import './ResultPreview.css'

function ResultPreview({ data, jobId, onReset }) {
  const handleDownload = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/download/${jobId}`)
      const blob = await response.blob()
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `dubbed_${data.filename || 'video'}.mp4`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Download failed:', error)
      alert('Download failed. Please try again.')
    }
  }

  return (
    <div className="result-preview">
      <div className="result-header">
        <div className="success-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
            <polyline points="22 4 12 14.01 9 11.01"></polyline>
          </svg>
        </div>
        <h2 className="result-title">Processing Complete</h2>
        <p className="result-subtitle">
          Video has been successfully dubbed and is ready for download
        </p>
      </div>

      <div className="result-info">
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Source Language</span>
            <span className="info-value">
              {data.source_language || 'Auto-detected'}
            </span>
          </div>
          
          <div className="info-item">
            <span className="info-label">Target Language</span>
            <span className="info-value">
              {data.target_language || 'N/A'}
            </span>
          </div>
          
          <div className="info-item">
            <span className="info-label">Processing Time</span>
            <span className="info-value">
              {data.processing_time || 'N/A'}
            </span>
          </div>
          
          <div className="info-item">
            <span className="info-label">File Name</span>
            <span className="info-value">
              {data.filename || 'video.mp4'}
            </span>
          </div>
        </div>
      </div>

      <div className="result-actions">
        <button 
          className="btn btn-primary btn-large"
          onClick={handleDownload}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          Download Video
        </button>
        
        <button 
          className="btn btn-secondary btn-large"
          onClick={onReset}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="1 4 1 10 7 10"></polyline>
            <polyline points="23 20 23 14 17 14"></polyline>
            <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
          </svg>
          Process Another Video
        </button>
      </div>

      <div className="result-footer">
        <p className="footer-text">
          Note: Review video quality before distribution. Dubbed videos are automatically deleted after 24 hours.
        </p>
      </div>
    </div>
  )
}

export default ResultPreview
