import React from "react";
import ParameterForm from "./ParameterForm";
import ResultsChart from "./ResultsChart";

const Simulation = ({ onSubmit, results }) => {
  return (
    <div className="w-full bg-gray-50 p-6 rounded border border-gray-700 shadow mt-6 mb-6">
      <ParameterForm onSubmit={onSubmit} />
      {results && (
        <div className="w-full bg-white p-6 rounded border border-gray-700 shadow mt-6">
          <div className="max-w-6xl mx-auto">
            <ResultsChart samples={results.samples} summary={results.summary} />
          </div>
        </div>
      )}
    </div>
  );
};

export default Simulation;