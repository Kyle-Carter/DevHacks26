import { useState, useEffect } from 'react'
import './GameDashboard.css'

const GAMES = [
    {
        id: 1,
        name: 'Pacman',
        description: 'Navigate the maze and eat all the dots',
        url: 'https://www.google.com/logos/2010/pacman10-i.html',
        thumbnail: '👾',
        controls: ['Move Left', 'Move Right', 'Jump', 'Squat']
    },
    {
        id: 2,
        name: 'Subway Surfers',
        description: 'Run through the subway, dodge trains!',
        url: 'https://poki.com/en/g/subway-surfers',
        thumbnail: '🏃',
        controls: ['Move Left', 'Move Right', 'Jump', 'Squat']
    }
]

export default function GameDashboard() {
    const [isConnected, setIsConnected] = useState(false)
    const [isRunning, setIsRunning] = useState(false)
    const [ws, setWs] = useState(null)

    useEffect(() => {
        return () => {
            if (ws) ws.close()
        }
    }, [ws])

    const handleToggleBackend = () => {
        if (!isRunning) {
            // Connect to Python backend
            const socket = new WebSocket('ws://localhost:8765')

            socket.onopen = () => {
                setIsConnected(true)
                setIsRunning(true)
                // Send current mappings
                const mappings = localStorage.getItem('movementMappings')
                if (mappings) {
                    socket.send(JSON.stringify({ type: 'config', mappings: JSON.parse(mappings) }))
                }
            }

            socket.onclose = () => {
                setIsConnected(false)
                setIsRunning(false)
            }

            socket.onerror = () => {
                setIsConnected(false)
                setIsRunning(false)
                alert('Could not connect to backend. Make sure to run: python backend/main.py')
            }

            setWs(socket)
        } else {
            // Disconnect
            if (ws) {
                ws.send(JSON.stringify({ type: 'stop' }))
                ws.close()
            }
            setIsRunning(false)
            setIsConnected(false)
        }
    }

    const handlePlayGame = (url) => {
        window.open(url, '_blank')
    }

    return (
        <div className="dashboard">
            <div className="page-header">
                <h1 className="page-title">Game Library</h1>
                <p className="page-subtitle">Select a game and start moving!</p>
            </div>

            <div className="control-panel card">
                <div className="control-info">
                    <h3>Motion Controls</h3>
                    <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
                        <span className="status-dot"></span>
                        {isConnected ? 'Connected' : 'Disconnected'}
                    </div>
                </div>
                <button
                    className={`btn ${isRunning ? 'btn-danger' : 'btn-success'}`}
                    onClick={handleToggleBackend}
                >
                    {isRunning ? '⏹ Stop' : '▶ Start'} Motion Detection
                </button>
            </div>

            <div className="games-grid">
                {GAMES.map(game => (
                    <div key={game.id} className="game-card card">
                        <div className="game-thumbnail">{game.thumbnail}</div>
                        <div className="game-info">
                            <h3 className="game-name">{game.name}</h3>
                            <p className="game-description">{game.description}</p>
                            <div className="game-controls">
                                {game.controls.map(control => (
                                    <span key={control} className="control-tag">{control}</span>
                                ))}
                            </div>
                        </div>
                        <button
                            className="btn btn-primary play-btn"
                            onClick={() => handlePlayGame(game.url)}
                        >
                            Play Now
                        </button>
                    </div>
                ))}
            </div>
        </div>
    )
}
