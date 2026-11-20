import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { startOffline } from './offline'
import './styles.css'

// Load offline data first so the first render already shows it (also offline).
void startOffline().then(() => {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
})
