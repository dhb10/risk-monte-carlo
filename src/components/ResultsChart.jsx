import Plot from "react-plotly.js";
import React from 'react'

const ResultsChart = ({ samples, summary }) => {
  if (!samples?.length) return null;

  return (
    
    <div className="mt-0 w-full">
      <h3 className="font-bold">Results</h3>
      <p>Mean: ${summary.mean.toFixed(2)}</p>
      <p>5th percentile: ${summary.percentile_5.toFixed(2)}</p>
      <p>95th percentile: ${summary.percentile_95.toFixed(2)}</p>

      <Plot
        data={[
          {
            x: samples,
            type: "histogram",
            marker: { color: "#2B202a" }
          }
        ]}
        layout={{
          title: "Outcome Distribution",
          xaxis: { title: "Outcome" },
          yaxis: { title: "Frequency" },
          autosize: true
        }}
        useResizeHandler={true}
        style={{ width: "100%", height: "400px" }}
        config={{ responsive: true }}
      />
    </div>
  );
}

export default ResultsChart