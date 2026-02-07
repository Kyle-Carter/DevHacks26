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

    const [sensitivity, setSensitivity] = useState(() => {
        const saved = localStorage.getItem('movementSensitivity')
        return saved ? JSON.parse(saved) : {
            jumpSensitivity: 0.5,
            squatSensitivity: 0.5,
            sideSensitivity: 0.5,
            repeatDelay: 1.0,
            repeatInterval: 0.2
        }
    })

    useEffect(() => {
        localStorage.setItem('movementMappings', JSON.stringify(mappings))
    }, [mappings])

    useEffect(() => {
        localStorage.setItem('movementSensitivity', JSON.stringify(sensitivity))
    }, [sensitivity])

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
        localStorage.setItem('movementSensitivity', JSON.stringify(sensitivity))
        setSaved(true)
        setTimeout(() => setSaved(false), 2000)
    }

    const handleReset = () => {
        setMappings(DEFAULT_MAPPINGS)
        setSensitivity({
            jumpSensitivity: 0.5,
            squatSensitivity: 0.5,
            sideSensitivity: 0.5,
            repeatDelay: 1.0,
            repeatInterval: 0.2
        })
    }

    const getMovementForKey = (keyCode) => {
        const movementId = Object.keys(mappings).find(m => mappings[m] === keyCode)
        return movementId ? MOVEMENTS.find(m => m.id === movementId) : null
    }

    const handleSensitivityChange = (key, value) => {
        setSensitivity(prev => ({ ...prev, [key]: parseFloat(value) }))
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

                    <div className="sensitivity-section" style={{ marginTop: '2rem', borderTop: '1px solid #333', paddingTop: '1rem' }}>
                        <h3>Sensitivity & Tuning</h3>

                        <div className="setting-group">
                            <label>Jump Sensitivity ({sensitivity.jumpSensitivity})</label>
                            <input
                                type="range" min="0.1" max="1.0" step="0.05"
                                value={sensitivity.jumpSensitivity}
                                onChange={(e) => handleSensitivityChange('jumpSensitivity', e.target.value)}
                            />
                            <small>Lower = Easier to Jump</small>
                        </div>

                        <div className="setting-group">
                            <label>Squat Sensitivity ({sensitivity.squatSensitivity})</label>
                            <input
                                type="range" min="0.1" max="1.0" step="0.05"
                                value={sensitivity.squatSensitivity}
                                onChange={(e) => handleSensitivityChange('squatSensitivity', e.target.value)}
                            />
                            <small>Lower = Easier to Squat</small>
                        </div>

                        <div className="setting-group">
                            <label>Side Sensitivity ({sensitivity.sideSensitivity})</label>
                            <input
                                type="range" min="0.1" max="1.0" step="0.05"
                                value={sensitivity.sideSensitivity}
                                onChange={(e) => handleSensitivityChange('sideSensitivity', e.target.value)}
                            />
                            <small>Lower = Easier to Move Side</small>
                        </div>

                        <div className="setting-group">
                            <label>Hold Delay ({sensitivity.repeatDelay}s)</label>
                            <input
                                type="range" min="0.1" max="2.0" step="0.1"
                                value={sensitivity.repeatDelay}
                                onChange={(e) => handleSensitivityChange('repeatDelay', e.target.value)}
                            />
                            <small>Time before key repeats/holds</small>
                        </div>


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
