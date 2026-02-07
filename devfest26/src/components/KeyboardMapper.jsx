import './KeyboardMapper.css'

const KEYBOARD_LAYOUT = [
    // Row 1 - only showing relevant gaming keys
    [
        { key: 'w', code: 'KeyW', label: 'W', width: 1 }
    ],
    // Row 2
    [
        { key: 'a', code: 'KeyA', label: 'A', width: 1 },
        { key: 's', code: 'KeyS', label: 'S', width: 1 },
        { key: 'd', code: 'KeyD', label: 'D', width: 1 }
    ],
    // Spacer
    ['spacer'],
    // Arrow keys row 1
    [
        { key: 'ArrowUp', code: 'ArrowUp', label: '↑', width: 1 }
    ],
    // Arrow keys row 2
    [
        { key: 'ArrowLeft', code: 'ArrowLeft', label: '←', width: 1 },
        { key: 'ArrowDown', code: 'ArrowDown', label: '↓', width: 1 },
        { key: 'ArrowRight', code: 'ArrowRight', label: '→', width: 1 }
    ],
    // Spacer
    ['spacer'],
    // Space bar
    [
        { key: 'Space', code: 'Space', label: 'SPACE', width: 4 }
    ]
]

export default function KeyboardMapper({ onKeyDrop, getMovementForKey, isDragging }) {
    const handleDragOver = (e) => {
        e.preventDefault()
        e.currentTarget.classList.add('drag-over')
    }

    const handleDragLeave = (e) => {
        e.currentTarget.classList.remove('drag-over')
    }

    const handleDrop = (e, keyCode) => {
        e.preventDefault()
        e.currentTarget.classList.remove('drag-over')
        onKeyDrop(keyCode)
    }

    return (
        <div className={`keyboard-mapper ${isDragging ? 'is-dragging' : ''}`}>
            {KEYBOARD_LAYOUT.map((row, rowIndex) => (
                <div key={rowIndex} className="keyboard-row">
                    {row[0] === 'spacer' ? (
                        <div className="keyboard-spacer"></div>
                    ) : (
                        row.map((keyData) => {
                            const movement = getMovementForKey(keyData.code)
                            return (
                                <div
                                    key={keyData.code}
                                    className={`keyboard-key ${movement ? 'has-movement' : ''}`}
                                    style={{ '--key-width': keyData.width }}
                                    onDragOver={handleDragOver}
                                    onDragLeave={handleDragLeave}
                                    onDrop={(e) => handleDrop(e, keyData.code)}
                                >
                                    <span className="key-label">{keyData.label}</span>
                                    {movement && (
                                        <div className="key-movement">
                                            <span className="movement-icon">{movement.icon}</span>
                                        </div>
                                    )}
                                </div>
                            )
                        })
                    )}
                </div>
            ))}
        </div>
    )
}
