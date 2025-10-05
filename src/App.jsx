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
import Toggle from "./components/Toggle";
import Simulation from "./components/Simulation";
import MultiScenarioResults from "./components/MultiScenarioResults"; 

const App = () => {
  const [results, setResults] = useState(null);
  const [selectedMode, setSelectedMode] = useState("Scenarios");
  const [isUploading, setIsUploading] = useState(false);
  const [resetFileTrigger, setResetFileTrigger] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [manualMode, setManualMode] = useState(false);

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
        // For scenarios, sending FormData (file upload), Content-Type optional but okay
        response = await axios.post(`${backendUrl}/scenarios`, formData, {
          // Axios/Browser will set boundaries if you omit the header,
          // but including it here is often harmless (less strict servers)
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
        // For simulation: could be FormData (file upload) or JSON (manual entry)
        let config = {};
        if (!(formData instanceof FormData)) {
          config.headers = { "Content-Type": "application/json" };
        }
        response = await axios.post(`${backendUrl}/simulate`, formData, config);
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

  const handleDownloadPdf = async () => {
    console.log('Results state for rendering:', results);
    if (!results || results.length === 0) {
      alert("No data available for download.");
      return;
    }
    try {
      const payload = { data: results };
      const res = await axios.post(`${backendUrl}/generate_pdf`, payload, {
        headers: { "Content-Type": "application/json" },
        responseType: "blob"
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "risk_scenarios.pdf");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error("Error downloading the PDF: ", error);
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
    if (results) {
      // If results is an array AND each entry has scenario keys, assume "multi-scenario" result
      if (Array.isArray(results) && results.length > 0 && results[0].scenario) {
        return (
          <div className="w-full mt-8 mb-8">
            <MultiScenarioResults scenarios={results} />
            <hr className="mt-8"></hr>
          </div>
        );
      }
      // If in manual simulation mode and results is a single simulation object
      if (manualMode && results.samples && results.summary) {
        return (
          <div className="w-full mt-8 mb-8">
            <ResultsChart samples={results.samples} summary={results.summary} />
            <hr className="mt-8"></hr>
          </div>
        );
      }
    }
    return null;
  }

  return (
    <div className="flex flex-col items-center min-h-screen bg-gray-100 px-4 sm:px-8">
      <div className="flex flex-col items-center mb-2 mt-12">
        <img src={logo} alt="Logo" className="w-64 h-auto mb-2" />
        <h2 className="text-xl font-bold text-black text-center tracking-wide uppercase mb-4 mt-2">
          RISK SCENARIOS & MONTE CARLO SIMULATION
        </h2>
        <hr className="w-full border-t border-gray-500 print:hidden" />

        {/* mode buttons */}
        <div className="flex justify-center my-4 gap-4">
          <Button
            onClick={() => {
              setSelectedMode("Scenarios");
              setManualMode(false); // Reset manual toggle when changing mode
            }}
            className={
              selectedMode === "Scenarios"
                ? "bg-gray-700 text-white"
                : "bg-gray-200 text-black"
            }
          >
            SCENARIOS
          </Button>
          <Button
            onClick={() => {setSelectedMode("Simulation"); setResults(null);} }
            className={
              selectedMode === "Simulation"
                ? "bg-gray-700 text-white"
                : "bg-gray-200 text-black"
            }
          >
            SIMULATION
          </Button>
        </div>
        {selectedMode === "Simulation" && (
          <div className="flex justify-center mb-4">
            <Toggle
              isOn={manualMode}
              onToggle={() => setManualMode(v => !v)}
              label="Manual Monte Carlo Input"
            />
          </div>
        )}
        <hr className="w-full border-t border-gray-500 print:hidden" />
      </div>

      {/* upload to identify scenarios */}
      <div className="w-full max-w-5xl mb-8">
        {selectedMode === "Scenarios" && (
          <div className="w-full mx-auto">
            {(!results || results.length === 0) && (
              <RiskUpload
                onSubmit={formData => handleSubmit(formData, "Scenarios")}
                isLoading={isUploading}
                resetFileTrigger={resetFileTrigger}
                clearResetFileTrigger={clearResetFileTrigger}
                mode="Scenarios"
              />
            )}
            {renderResults()}
            <ResultsButtons
              response={results}
              handleReset={handleReset}
              handleDownload={handleDownload}
              handleDownloadPdf={handleDownloadPdf}
              isLoading={isLoading}
            />
          </div>
        )}

        {/* upload and manual simulation */}
        {selectedMode === "Simulation" && (
          <div className="w-full mx-auto">
            {/* If not manual mode, show risk upload */}
            {!manualMode && (!results || results.length === 0) && (
              <RiskUpload
                onSubmit={formData => handleSubmit(formData, "Simulation")}
                isLoading={isUploading}
                resetFileTrigger={resetFileTrigger}
                clearResetFileTrigger={clearResetFileTrigger}
                mode="Simulation"
              />
            )}

            {manualMode && (
              <Simulation
                onSubmit={formData => handleSubmit(formData, "Simulation") }
                results={results}
              />
            )}
            {renderResults()}
          </div>
        )}
      </div>
    </div>
  );
};

export default App;