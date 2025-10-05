import React from "react";
import ScenarioResultsChart from "./ScenarioResultsChart";

const MultiScenarioResults = ({ scenarios }) => {
  if (!scenarios?.length) return null;

  return (
    <div className="flex flex-col gap-4">
      {scenarios.map((scenario, idx) => (
        <div key={idx} className="w-full">
          <ScenarioResultsChart scenario={scenario} />
        </div>
      ))}
    </div>
  );
};

export default MultiScenarioResults;