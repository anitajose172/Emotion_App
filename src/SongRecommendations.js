import React from 'react'

export default function SongRecommendations({ recommendations }) {
    return (
        <div>
            <h3>Song Recommendations:</h3>
            <ul>
                {recommendations.map((song, index) => (
                    <li key={index}>{song.name} - {song.artist}</li> 
                ))}
            </ul>
        </div>
    );
}

