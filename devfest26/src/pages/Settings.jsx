import { useState, useEffect } from 'react'
import KeyboardMapper from '../components/KeyboardMapper'
import MovementCard from '../components/MovementCard'
import './Settings.css'

const MOVEMENTS = [
    { id: 'jump', name: 'Jump', icon: '🦘', description: 'Jump upward' },
    { id: 'squat', name: 'Squat', icon: '🧎', description: 'Crouch down' },
    { id: 'moveLeft', name: 'Move Left', icon: '👈', description: 'Lean left' },
    { id: 'moveRight', name: 'Move Right', icon: '👉', description: 'Lean right' }
]

const DEFAULT_MAPPINGS = {
    jump: 'Space',
    squat: 'ArrowDown',
    moveLeft: 'ArrowLeft',
    moveRight: 'ArrowRight'
}

export default function Settings() {
    const [mappings, setMappings] = useState(() => {
        const saved = localStorage.getItem('movementMappings')
        return saved ? JSON.parse(saved) : DEFAULT_MAPPINGS
    })
    const [draggedMovement, setDraggedMovement] = useState(null)
    const [saved, setSaved] = useState(false)

    useEffect(() => {
        localStorage.setItem('movementMappings', JSON.stringify(mappings))
    }, [mappings])

    const handleDragStart = (movementId) => {
        setDraggedMovement(movementId)
    }

    const handleDragEnd = () => {
        setDraggedMovement(null)
    }

    const handleKeyDrop = (keyCode) => {
        if (draggedMovement) {
            // Remove any existing mapping for this key
            const newMappings = { ...mappings }
            Object.keys(newMappings).forEach(m => {
                if (newMappings[m] === keyCode) {
                    newMappings[m] = null
                }
            })
            // Set new mapping
            newMappings[draggedMovement] = keyCode
            setMappings(newMappings)
            setDraggedMovement(null)
        }
    }

    const handleClearMapping = (movementId) => {
        setMappings(prev => ({ ...prev, [movementId]: null }))
    }

    const handleSave = () => {
        localStorage.setItem('movementMappings', JSON.stringify(mappings))
        setSaved(true)
        setTimeout(() => setSaved(false), 2000)
    }

    const handleReset = () => {
        setMappings(DEFAULT_MAPPINGS)
    }

    const getMovementForKey = (keyCode) => {
        const movementId = Object.keys(mappings).find(m => mappings[m] === keyCode)
        return movementId ? MOVEMENTS.find(m => m.id === movementId) : null
    }

    return (
        <div className="settings">
            <div className="page-header">
                <h1 className="page-title">Control Settings</h1>
                <p className="page-subtitle">Drag movements onto keyboard keys to map your controls</p>
            </div>

            <div className="settings-layout">
                <div className="movements-panel card">
                    <h3>Movements</h3>
                    <p className="panel-hint">Drag a movement to a key</p>
                    <div className="movements-list">
                        {MOVEMENTS.map(movement => (
                            <MovementCard
                                key={movement.id}
                                movement={movement}
                                mappedKey={mappings[movement.id]}
                                onDragStart={() => handleDragStart(movement.id)}
                                onDragEnd={handleDragEnd}
                                onClear={() => handleClearMapping(movement.id)}
                                isDragging={draggedMovement === movement.id}
                            />
                        ))}
                    </div>
                </div>

                <div className="keyboard-panel card">
                    <h3>Keyboard</h3>
                    <p className="panel-hint">Drop movements on keys to bind them</p>
                    <KeyboardMapper
                        onKeyDrop={handleKeyDrop}
                        getMovementForKey={getMovementForKey}
                        isDragging={!!draggedMovement}
                    />
                </div>
            </div>

            <div className="settings-actions">
                <button className="btn btn-secondary" onClick={handleReset}>
                    Reset to Defaults
                </button>
                <button className={`btn btn-primary ${saved ? 'saved' : ''}`} onClick={handleSave}>
                    {saved ? '✓ Saved!' : 'Save Settings'}
                </button>
            </div>
        </div>
    )
}
