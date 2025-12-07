import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [message, setMessage] = useState('Click to test backend connection')
  const [loading, setLoading] = useState(false)

  const testConnection = async () => {
    setLoading(true)
    try {
      const response = await axios.get('http://localhost:8000/healthz')
      setMessage(`✅ Backend connected: ${JSON.stringify(response.data)}`)
    } catch (error) {
      setMessage(`❌ Error connecting to backend: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ 
      padding: '2rem', 
      maxWidth: '800px', 
      margin: '0 auto',
      fontFamily: 'system-ui, sans-serif'
    }}>
      <h1 style={{ color: '#333' }}>🌐 Universal Website Scraper</h1>
      <p style={{ color: '#666' }}>Full-stack assignment for Lyftr AI</p>
      
      <div style={{ 
        margin: '2rem 0', 
        padding: '1.5rem',
        backgroundColor: '#f5f5f5',
        borderRadius: '8px'
      }}>
        <h3>Setup Test</h3>
        <button 
          onClick={testConnection}
          disabled={loading}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: loading ? '#ccc' : '#007acc',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '1rem',
            marginTop: '1rem'
          }}
        >
          {loading ? 'Testing...' : 'Test Backend Connection'}
        </button>
        <p style={{ 
          marginTop: '1rem',
          padding: '0.75rem',
          backgroundColor: message.includes('✅') ? '#e6f7e6' : '#ffe6e6',
          borderRadius: '4px'
        }}>
          {message}
        </p>
      </div>

      <div style={{ marginTop: '2rem' }}>
        <h3>Next Steps:</h3>
        <ul>
          <li>✅ Python packages installed</li>
          <li>✅ FastAPI backend setup</li>
          <li>✅ React frontend setup</li>
          <li>🔜 Implement scraping logic</li>
          <li>🔜 Add URL input form</li>
          <li>🔜 Display scraped results</li>
        </ul>
      </div>
    </div>
  )
}

export default App