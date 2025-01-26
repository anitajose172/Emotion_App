import React from 'react'

export default function EmotionDisplay({ emotion }) {
  return (
    <div>
            {emotion && <h2>Detected Emotion: {emotion}</h2>}
    </div>
  )
}
