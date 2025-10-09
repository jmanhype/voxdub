import { useState, useEffect } from 'react'
import './LanguageSelector.css'

function LanguageSelector({ selectedLanguage, onLanguageChange }) {
  const [languages, setLanguages] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchLanguages()
  }, [])

  const fetchLanguages = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/languages')
      const data = await response.json()
      setLanguages(data.languages || [])
    } catch (error) {
      console.error('Failed to fetch languages:', error)
      setLanguages([
        { code: 'en', name: 'English', native: 'English' },
        { code: 'es', name: 'Spanish', native: 'Español' },
        { code: 'fr', name: 'French', native: 'Français' },
        { code: 'de', name: 'German', native: 'Deutsch' },
        { code: 'hi', name: 'Hindi', native: 'हिन्दी' },
        { code: 'zh', name: 'Chinese', native: '中文' },
        { code: 'ja', name: 'Japanese', native: '日本語' },
        { code: 'ko', name: 'Korean', native: '한국어' },
        { code: 'pt', name: 'Portuguese', native: 'Português' },
        { code: 'ru', name: 'Russian', native: 'Русский' },
        { code: 'ar', name: 'Arabic', native: 'العربية' },
        { code: 'it', name: 'Italian', native: 'Italiano' }
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="language-selector">
      <label htmlFor="language" className="selector-label">
        Target Language
      </label>
      
      <div className="selector-wrapper">
        <select
          id="language"
          value={selectedLanguage}
          onChange={(e) => onLanguageChange(e.target.value)}
          className="language-select"
          disabled={loading}
        >
          {loading ? (
            <option>Loading languages...</option>
          ) : (
            languages.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.name} ({lang.native})
              </option>
            ))
          )}
        </select>
      </div>
      
      <p className="selector-hint">
        Select the language for dubbed audio output
      </p>
    </div>
  )
}

export default LanguageSelector
