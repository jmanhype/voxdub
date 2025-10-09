import { useEffect, useState } from 'react'
import './ProcessingStatus.css'

function ProcessingStatus({ data }) {
  const [dots, setDots] = useState('.')

  useEffect(() => {
    const interval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '.' : prev + '.')
    }, 500)
    
    return () => clearInterval(interval)
  }, [])

  const steps = [
    { id: 1, name: 'Extracting audio', key: 'audio' },
    { id: 2, name: 'Transcribing speech', key: 'transcribe' },
    { id: 3, name: 'Translating text', key: 'translate' },
    { id: 4, name: 'Generating speech', key: 'synthesis' },
    { id: 5, name: 'Syncing lips', key: 'lipsync' }
  ]

  const getCurrentStep = () => {
    if (!data || !data.current_step) return 0
    const stepText = data.current_step.toLowerCase()
    
    if (stepText.includes('audio')) return 1
    if (stepText.includes('transcrib')) return 2
    if (stepText.includes('translat')) return 3
    if (stepText.includes('speech') || stepText.includes('generat')) return 4
    if (stepText.includes('lip') || stepText.includes('sync')) return 5
    
    return 0
  }

  const currentStepNum = getCurrentStep()
  const progress = data?.progress || 0

  return (
    <div className="processing-status">
      <div className="status-header">
        <div className="status-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
        </div>
        <h2 className="status-title">Processing Video{dots}</h2>
        <p className="status-subtitle">
          {data?.current_step || 'Starting processing...'}
        </p>
      </div>

      <div className="progress-bar-container">
        <div 
          className="progress-bar-fill"
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="progress-text">{progress}% Complete</p>

      <div className="steps-list">
        {steps.map((step) => {
          const isComplete = step.id < currentStepNum
          const isCurrent = step.id === currentStepNum
          const isPending = step.id > currentStepNum

          return (
            <div 
              key={step.id}
              className={`step-item ${isComplete ? 'complete' : ''} ${isCurrent ? 'current' : ''} ${isPending ? 'pending' : ''}`}
            >
              <div className="step-indicator">
                {isComplete && (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                )}
                {isCurrent && (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                  </svg>
                )}
                {isPending && (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                  </svg>
                )}
              </div>
              <span className="step-name">{step.name}</span>
            </div>
          )
        })}
      </div>

      <div className="status-info">
        <p className="info-text">
          Processing time varies based on video length. Typical duration: 2-5 minutes.
        </p>
      </div>
    </div>
  )
}

export default ProcessingStatus
