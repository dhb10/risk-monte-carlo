import React from 'react';

const Toggle = ({ isOn, onToggle, isDisabled, className = '' }) => (
    <button
        onClick={() => {
            if (!isDisabled) onToggle(!isOn);
        }}
        disabled={isDisabled}
        className={`
            relative inline-flex items-center h-10 px-1 w-20 rounded-full transition-colors duration-300
            ${isDisabled ? 'bg-gray-400 cursor-not-allowed' : isOn ? 'bg-black' : 'bg-gray-300'}
            ${className}
        `}
    >
        <span
            className={`
                inline-block w-8 h-8 transform bg-white px-2 rounded-full shadow-md transition-transform duration-300
                ${isOn ? 'translate-x-10' : 'translate-x-0'}
            `}
        />
    </button>

);

export default Toggle;