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

  const handleTemplateDownload = (fileName) => {
    const link = document.createElement("a");
    link.href = `/${fileName}`;
    link.setAttribute("download", fileName);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

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
          // Axios/Browser will set boundaries if you omit the header,
          // but including it here is often harmless (less strict servers)
          headers: { "Content-Type": "multipart/form-data" }
        });
        //start polling
        if (response.data && response.data.task_id) {
          setIsLoading(true);
          checkTaskStatus(response.data.task_id);
        } else {
          setResults(response.data);
        }
      } else {
        //could be form data or json for the manual entry
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
    if (!results || results.length === 0) {
      alert("No data available for download.");
      return;
    }
    try {
      const payload = { data: results };
      // Choose endpoint based on mode
      let endpoint;
      let filename;

      if (selectedMode === "Scenarios") {
        endpoint = "/generate_pdf";
        filename = "risk_scenarios.pdf";
      } else if (selectedMode === "Simulation") {
        endpoint = "/simulation_pdf";
        filename = "simulation_results.pdf";
      } else {
        alert("PDF download not supported for this mode.");
        return;
      }

      const res = await axios.post(`${backendUrl}${endpoint}`, payload, {
        headers: { "Content-Type": "application/json" },
        responseType: "blob"
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename);
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
      // Render multi-scenario results or scenario results based on mode and presence of data
      if (selectedMode === "Scenarios") {
        // If an array of results - probably from scenarios mode
        if (Array.isArray(results) && results.length > 0) {
          return (
            <div className="w-full mt-8 mb-8">
              <ResultsComponent response={results} />
              <hr className="mt-8"></hr>
            </div>
          );
        }
      }
      if (selectedMode === "Simulation") {
        // If in manual simulation mode and results is a single simulation object
        if (manualMode && results.samples && results.summary) {
          return (
            <div className="w-full mt-8 mb-8">
              <ResultsChart samples={results.samples} summary={results.summary} />
              <hr className="mt-8"></hr>
            </div>
          );
        }
        // If an array of simulations, render MultiScenarioResults (if wanted)
        if (Array.isArray(results) && results.length > 0 && results[0].scenario) {
          return (
            <div className="w-full mt-8 mb-8">
              <MultiScenarioResults scenarios={results} />
              <hr className="mt-8"></hr>
            </div>
          );
        }
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
        {/* template file download buttons */}
        <div className="flex w-full max-w-xl justify-center mt-4 gap-4">
          <Button
            onClick={() => handleTemplateDownload('risk_scenario_id-TEMPLATE.csv')}
          >
            SCENARIO TEMPLATE
          </Button>
          <Button
            onClick={() => handleTemplateDownload('risk_scenario_monte_carlo-TEMPLATE.xlsx')}
          >
            SIMULATION TEMPLATE
          </Button>
        </div>
        <hr className="w-full border-t my-4 border-gray-500 print:hidden" />
        {/* mode buttons */}
        <div className="flex w-full max-w-xl justify-center my-4 gap-4">
          <Button
            onClick={() => {
              handleReset();
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
            onClick={() => {
              handleReset();
              setSelectedMode("Simulation");} }
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
              onToggle={() => {
                handleReset();
                setManualMode(v => !v);
              }}
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
              selectedMode={selectedMode}
            />
          </div>
        )}

        {/* upload and manual simulation */}
        {selectedMode === "Simulation" && (
          <div className="w-full mx-auto">
            {/* Show risk upload only if not manualMode and no results */}
            {!manualMode && (!results || results.length === 0) && (
              <RiskUpload
                onSubmit={formData => handleSubmit(formData, "Simulation")}
                isLoading={isUploading}
                resetFileTrigger={resetFileTrigger}
                clearResetFileTrigger={clearResetFileTrigger}
                mode="Simulation"
              />
            )}

            {/* Manual mode shows Simulation card, NOT renderResults */}
            {manualMode && (
              <Simulation
                onSubmit={formData => handleSubmit(formData, "Simulation")}
                results={results}
              />
            )}

            {/* Only show results (including multiscenario) if NOT manualMode */}
            {!manualMode && renderResults()}

            <ResultsButtons
              response={results}
              handleReset={handleReset}
              handleDownload={handleDownload}
              handleDownloadPdf={handleDownloadPdf}
              isLoading={isLoading}
              selectedMode={selectedMode}
              manualMode={manualMode}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default App;