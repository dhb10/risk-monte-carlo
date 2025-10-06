import Plot from "react-plotly.js";
import React from "react";

const ScenarioResultsChart = ({ scenario }) => (
  <div className="mt-4 w-full border rounded-lg p-4 mb-4 bg-white shadow">
    <div className="mb-2">
      <h3 className="font-bold text-lg mb-2">{scenario.risk}</h3>
      <div>
        <div className="mb-2">
          <span className="font-semibold text-md">Scenario:<br></br></span>
          <span className="font-semibold text-md mr-4">{scenario.scenario}</span>
        </div>
        {scenario.formula && (
          <div>
            <hr></hr>
            <div className="mt-4 mb-4">
              <span className="font-semibold">Formula:<br></br></span>
              <span className="font-semibold">
                {scenario.formula_equals
                  ? `${scenario.formula_equals} = ${scenario.formula}`
                  : scenario.formula}
              </span>
            </div>
            <hr></hr>
          </div>
        )}

        <div className="mt-4 mb-4">
          {/* <span className="font-semibold block mb-2">Variables:</span> */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {scenario.variables && scenario.variables.map((v, i) => (
              <div
                key={i}
                className="bg-gray-100 border border-gray-700 rounded-lg p-3 shadow-sm"
              >
                <div className="font-mono text-s font-semibold mb-1">{v.name}</div>
                <div className="text-s mb-2 text-gray-700">Distribution: {v.distribution}</div>
                <ul className="ml-6 text-s list-disc">
                  {Object.entries(v.parameters).map(([param, val]) => (
                    <li key={param}>
                      <span className="font-mono">{param}: {val}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <div className="mt-4"><hr /></div>
        </div>

      </div>
    </div>
    <div className="">
      <p>Mean: <span className="">${scenario.summary.mean.toFixed(2)}</span></p>
      <p>5th percentile: <span className="">${scenario.summary.percentile_5.toFixed(2)}</span></p>
      <p>95th percentile: <span className="">${scenario.summary.percentile_95.toFixed(2)}</span></p>
    </div>
    <Plot
      data={[{
        x: scenario.samples,
        type: "histogram",
        marker: { color: "#2B303a" }
      }]}
      layout={{
        title: "Outcome Distribution",
        xaxis: { title: "Outcome" },
        yaxis: { title: "Frequency" },
        autosize: true
      }}
      useResizeHandler={true}
      style={{ width: "100%", height: "500px" }}
      config={{ responsive: true }}
    />
  </div>
);

export default ScenarioResultsChart;