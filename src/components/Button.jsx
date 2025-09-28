import React from 'react';

function Button({ onClick, isSelected, isDisabled = false, children, className = '' }) {
  return (
    <button
      onClick={!isDisabled ? onClick : undefined}
      disabled={isDisabled}
      className={`w-full min-w-[200px] sm:w-auto px-4 py-4 rounded text-center text-sm sm:text-base
        ${isDisabled ? 'bg-gray-400 text-gray-700 cursor-not-allowed' : 'hover:bg-black hover:text-white'}
        ${isSelected ? 'bg-[#2b303a] text-white' : 'bg-gray-300 text-[#2b303a]'} ${className}`}
    >
      {children}
    </button>
  );
}


export default Button;