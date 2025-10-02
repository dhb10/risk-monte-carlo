import React from "react";

const distributionFields = {
  normal: ["mean", "stddev"],
  triangular: ["min", "mode", "max"],
  uniform: ["min", "max"],
  lognormal: ["mean", "stddev"]
};

const capitalize = (str) => str.toUpperCase();

const ParameterInput = ({ variable, index, onChange, onDelete, showDelete }) => {
  const handleFieldChange = (field, value) => {
    const updated = {
      ...variable,
      parameters: { ...variable.parameters, [field]: parseFloat(value) }
    };
    onChange(index, updated);
  };

  const handleNameChange = (e) => {
    onChange(index, { ...variable, name: e.target.value });
  };

  const handleDistChange = (e) => {
    const newDist = e.target.value;
    const fields = distributionFields[newDist];
    const newParams = {};
    fields.forEach((field) => {
      newParams[field] = 0;
    });
    onChange(index, {
      ...variable,
      distribution: newDist,
      parameters: newParams
    });
  };

  return (
    <div className="relative bg-white border border-gray-700 shadow-md rounded-md p-4 mb-4">
        {showDelete && (
        <button
          type="button"
          className="absolute top-1 right-2 text-gray-700 hover:text-red-500 text-lg font-bold"
          onClick={onDelete}
          aria-label="Remove variable"
        >
          ×
        </button>
      )}
      {/* Variable name label & input */}
      <label className="block text-xs text-left font-bold mb-1 tracking-wider text-gray-700">
        VARIABLE NAME
      </label>
      <input
        type="text"
        placeholder=""
        className="block w-full mb-2 p-2 border border-gray-700 rounded focus:outline-none focus:border-gray-700 focus:ring-1 focus:ring-gray-700"
        value={variable.name}
        onChange={handleNameChange}
      />

      {/* Distribution label & select */}
      <label className="block text-xs text-left font-bold mb-1 tracking-wider text-gray-700">
        DISTRIBUTION
      </label>
      <select
        className="block w-full mb-2 p-2 border border-gray-700 rounded focus:outline-none focus:border-gray-700 focus:ring-1 focus:ring-gray-700"
        value={variable.distribution}
        onChange={handleDistChange}
      >
        <option value=""></option>
        {Object.keys(distributionFields).map((dist) => (
          <option key={dist} value={dist}>
            {dist.charAt(0).toUpperCase() + dist.slice(1)}
          </option>
        ))}
      </select>

      {/* Parameter fields, dynamically labeled and uppercased */}
      {distributionFields[variable.distribution]?.map((field) => (
        <div key={field}>
          <label className="block text-xs font-bold mb-1 text-left tracking-wider text-gray-700">
            {capitalize(field)}
          </label>
          <input
            type="number"
            className="block w-full mb-2 p-2 border border-gray-700 rounded focus:outline-none focus:border-gray-700 focus:ring-1 focus:ring-gray-700"
            // placeholder={field}
            value={variable.parameters[field] ?? ""}
            onChange={(e) => handleFieldChange(field, e.target.value)}
          />
        </div>
      ))}
    </div>
  );
};

export default ParameterInput;