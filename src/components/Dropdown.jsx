import React from "react";

const Dropdown = ({ selected, onSelect, disabled = false }) => {
  const distributions = [
    "normal",
    "triangular",
    "uniform",
    "lognormal"
  ];

  const handleSelect = (event) => {
    const value = event.target.value;
    onSelect(value);
  };

  return (
    <div className="mb-4">
      <label
        htmlFor="distribution-select"
        className="block text-sm font-medium text-gray-700 text-center mb-3"
      >
        CHOOSE DISTRIBUTION:
      </label>
      <select
        id="distribution-select"
        onChange={handleSelect}
        className="block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring focus:border-blue-300 disabled:bg-gray-100 disabled:cursor-not-allowed"
        value={selected ?? ""}
        disabled={disabled}
      >
        <option value="" disabled>Select a distribution</option>
        {distributions.map((dist) => (
          <option key={dist} value={dist}>
            {dist.charAt(0).toUpperCase() + dist.slice(1)}
          </option>
        ))}
      </select>
    </div>
  );
};

export default Dropdown;



