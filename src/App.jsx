import React, { useState, Suspense } from "react";
import axios from "axios";
import ParameterForm from "./components/ParameterForm";
import ResultsChart from "./components/ResultsChart";
import RiskUpload from "./components/RiskUpload";
import Button from "./components/Button";
import logo from "./assets/logo.png";
import spinner from './assets/spinner.gif';
import ResultsButtons from './components/ResultsButtons';
import ResultsComponent from "./components/ResultsComponent";

const App = () => {
  const [results, setResults] = useState(null);
  const [selectedMode, setSelectedMode] = useState("Scenarios");
  const [isUploading, setIsUploading] = useState(false);
  const [resetFileTrigger, setResetFileTrigger] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const backendUrl = "http://localhost:5000";

  const handleSubmit = async (formData, mode) => {
    if (mode === "Scenarios") {
      setIsUploading(true);
      setResults(null);
      setIsLoading(false);
    } else {
      setResults(null);
      setIsLoading(false);
    }
    try {
      let response;
      if (mode === "Scenarios") {
        response = await axios.post(`${backendUrl}/scenarios`, formData, {
          headers: { "Content-Type": "multipart/form-data" }
        });
        // if async (returns task id), start polling:
        if (response.data && response.data.task_id) {
          setIsLoading(true);
          checkTaskStatus(response.data.task_id);
        } else {
          setResults(response.data);
        }
      } else {
        response = await axios.post(`${backendUrl}/simulate`, formData, {
          headers: { "Content-Type": "application/json" }
        });
        setResults(response.data);
      }
    } catch (error) {
      console.error("Submission failed:", error);
    } finally {
      if (mode === "Scenarios") {
        setIsUploading(false);
      }
    }
  };

  const checkTaskStatus = async (taskId) => {
    try {
      const res = await axios.get(`${backendUrl}/task_status/${taskId}`);
      const { state, result } = res.data;
      if (state === "SUCCESS") {
        setResults(result);
        setIsLoading(false);
      } else if (state === "FAILURE") {
        setIsLoading(false);
        alert('Task failed.');
      } else {
        setTimeout(() => checkTaskStatus(taskId), 3000);
      }
    } catch (error) {
      console.error("Error checking task status: ", error);
      setIsLoading(false);
      alert('Error retrieving task status.');
    }
  };

  const clearResetFileTrigger = () => setResetFileTrigger(false);

  const handleReset = () => {
    setResults(null);
    setResetFileTrigger(true);
    setIsUploading(false);
    setIsLoading(false);
  };

  const handleDownload = async () => {
    if (!results || results.length === 0) {
      alert("No data available for download.");
      return;
    }
    try {
      const payload = { data: results };
      const res = await axios.post(`${backendUrl}/generate_csv`, payload, {
        headers: { "Content-Type": "application/json" },
        responseType: "blob"
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "risk_scenarios.csv");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error("Error downloading the CSV: ", error);
    }
  };

  function renderResults() {
    if (isLoading) {
      return (
        <div className="w-full flex justify-center items-center mt-8">
          <img src={spinner} alt="Loading..." className="w-12 h-12" />
        </div>
      );
    }
    // Only render ResultsComponent if there is a non-empty results array
    if (results && results.length > 0) {
      return (
        <div className="w-full ml-2 mr-2 mt-8 mb-8">
          <Suspense fallback={<div> </div>}>
            <ResultsComponent response={results} />
          </Suspense>
          <hr className="mt-8"></hr>
        </div>
      );
    }
    return null; // If there is nothing to render
  }

  return (
    <div className="flex flex-col items-center min-h-screen bg-gray-100 px-4 sm:px-8">
      <div className="flex flex-col items-center mb-2 mt-12">
        <img src={logo} alt="Logo" className="w-64 h-auto mb-2" />
        <h2 className="text-xl font-bold text-black text-center tracking-wide uppercase mb-4 mt-2">
          MONTE CARLO RISK SIMULATION
        </h2>
        <hr className="w-full border-t border-gray-500 print:hidden" />

        {/* TAB BUTTONS */}
        <div className="flex justify-center my-4 gap-4">
          <Button onClick={() => setSelectedMode("Scenarios")}>
            SCENARIOS
          </Button>
          <Button onClick={() => setSelectedMode("Simulation")}>
            SIMULATION
          </Button>
        </div>
        <hr className="w-full border-t border-gray-500 print:hidden" />
      </div>

      {/* Container with max width */}
      <div className="w-full max-w-5xl mb-8">
        {selectedMode === "Scenarios" && (
          <div className="w-full mx-auto">
            {(!results || results.length === 0) && (
              <RiskUpload
                onSubmit={formData => handleSubmit(formData, "Scenarios")}
                isLoading={isUploading}
                resetFileTrigger={resetFileTrigger}
                clearResetFileTrigger={clearResetFileTrigger}
              />
            )}

            {renderResults()}

            <ResultsButtons
              response={results}
              handleReset={handleReset}
              handleDownload={handleDownload}
              isLoading={isLoading}
            />
          </div>
        )}

        {selectedMode === "Simulation" && (
          <div className="text-center">
            <ParameterForm onSubmit={handleSubmit} />
            {results && (
              <div className="w-full bg-white p-6 rounded shadow mt-6">
                <div className="max-w-6xl mx-auto">
                  <ResultsChart samples={results.samples} summary={results.summary} />
                </div>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
};

export default App;