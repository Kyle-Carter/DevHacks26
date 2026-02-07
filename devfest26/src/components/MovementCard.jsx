import './MovementCard.css'

const KEY_DISPLAY_NAMES = {
    'Space': 'SPACE',
    'ArrowUp': '↑',
    'ArrowDown': '↓',
    'ArrowLeft': '←',
    'ArrowRight': '→',
    'KeyW': 'W',
    'KeyA': 'A',
    'KeyS': 'S',
    'KeyD': 'D'
}

export default function MovementCard({
    movement,
    mappedKey,
    onDragStart,
    onDragEnd,
    onClear,
    isDragging
}) {
    return (
        <div
            className={`movement-card ${isDragging ? 'dragging' : ''} ${mappedKey ? 'mapped' : ''}`}
            draggable
            onDragStart={onDragStart}
            onDragEnd={onDragEnd}
        >
            <div className="movement-icon-wrapper">
                <span className="movement-icon">{movement.icon}</span>
            </div>
            <div className="movement-details">
                <span className="movement-name">{movement.name}</span>
                {mappedKey && (
                    <span className="movement-key">{KEY_DISPLAY_NAMES[mappedKey] || mappedKey}</span>
                )}
            </div>
            {mappedKey && (
                <button className="clear-btn" onClick={(e) => { e.stopPropagation(); onClear(); }}>
                    ✕
                </button>
            )}
        </div>
    )
}
