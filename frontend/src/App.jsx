import { useState } from 'react'
import './App.css'
import VideoUpload from './components/VideoUpload'
import LanguageSelector from './components/LanguageSelector'
import ProcessingStatus from './components/ProcessingStatus'
import ResultPreview from './components/ResultPreview'

function App() {
  const [step, setStep] = useState('upload')
  const [selectedLanguage, setSelectedLanguage] = useState('es')
  const [uploadedFile, setUploadedFile] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [processingData, setProcessingData] = useState(null)
  const [resultData, setResultData] = useState(null)

  const handleFileSelect = (file) => {
    setUploadedFile(file)
  }

  const handleStartDubbing = async () => {
    if (!uploadedFile) return

    setStep('processing')

    try {
      const formData = new FormData()
      formData.append('video', uploadedFile)
      formData.append('target_language', selectedLanguage)

      const response = await fetch('http://localhost:8000/api/dub', {
        method: 'POST',
        body: formData
      })

      const data = await response.json()
      
      if (data.job_id) {
        setJobId(data.job_id)
        pollJobStatus(data.job_id)
      }
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Processing failed. Please try again.')
      setStep('upload')
    }
  }

  const pollJobStatus = async (id) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/status/${id}`)
        const data = await response.json()
        
        setProcessingData(data)

        if (data.status === 'completed') {
          clearInterval(interval)
          setResultData(data)
          setStep('complete')
        } else if (data.status === 'failed') {
          clearInterval(interval)
          alert('Processing failed: ' + data.error)
          setStep('upload')
        }
      } catch (error) {
        console.error('Status check failed:', error)
      }
    }, 2000)
  }

  const handleReset = () => {
    setStep('upload')
    setUploadedFile(null)
    setJobId(null)
    setProcessingData(null)
    setResultData(null)
  }

  return (
    <div className="app">
      <header className="header">
        <div className="container">
          <div className="header-content">
            <div className="logo">
              <span className="logo-mark">VoxDub</span>
              <span className="logo-badge">AI</span>
            </div>
            <nav className="nav">
              <a href="#" className="nav-link">Documentation</a>
              <a href="#" className="nav-link">API</a>
            </nav>
          </div>
        </div>
      </header>

      <main className="main">
        <div className="container container-narrow">
          {step === 'upload' && (
            <div className="fade-in">
              <div className="hero">
                <h1 className="hero-title">
                  AI-Powered Video Dubbing
                </h1>
                <p className="hero-subtitle">
                  Professional multilingual dubbing with advanced lip synchronization.
                  Powered by Whisper AI, Meta NLLB, and Wav2Lip technology.
                </p>
              </div>

              <div className="workspace">
                <VideoUpload 
                  onFileSelect={handleFileSelect}
                  selectedFile={uploadedFile}
                />
                
                <LanguageSelector 
                  selectedLanguage={selectedLanguage}
                  onLanguageChange={setSelectedLanguage}
                />

                <button 
                  className="btn btn-primary btn-large"
                  onClick={handleStartDubbing}
                  disabled={!uploadedFile}
                >
                  Start Processing
                </button>

                <div className="features">
                  <div className="feature-item">
                    <span className="feature-label">Format Support</span>
                    <span className="feature-value">MP4, AVI, MOV, MKV</span>
                  </div>
                  <div className="feature-item">
                    <span className="feature-label">Max File Size</span>
                    <span className="feature-value">500 MB</span>
                  </div>
                  <div className="feature-item">
                    <span className="feature-label">Processing Time</span>
                    <span className="feature-value">2-5 minutes</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {step === 'processing' && (
            <ProcessingStatus data={processingData} />
          )}

          {step === 'complete' && (
            <ResultPreview 
              data={resultData}
              jobId={jobId}
              onReset={handleReset}
            />
          )}
        </div>
      </main>

      <footer className="footer">
        <div className="container">
          <div className="footer-content">
            <p className="footer-text">
              © 2025 VoxDub. Enterprise-grade video dubbing infrastructure.
            </p>
            <div className="footer-links">
              <a href="#" className="footer-link">Privacy Policy</a>
              <a href="#" className="footer-link">Terms of Service</a>
              <a href="#" className="footer-link">GitHub</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
