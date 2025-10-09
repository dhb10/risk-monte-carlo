import React, { useState } from "react";
import Button from "./Button";
import ParameterInput from "./ParameterInput";


const distributionFields = {
  normal: ["mean", "stddev"],
  triangular: ["min", "mode", "max"],
  uniform: ["min", "max"],
  lognormal: ["mean", "stddev"]
};

const ParameterForm = ({ onSubmit }) => {
  const [variables, setVariables] = useState([
    { name: "", distribution: "", parameters: {} }
  ]);
  const [formula, setFormula] = useState("");
  const [numTrials, setNumTrials] = useState(10000);

  const handleVariableChange = (index, updatedVariable) => {
    const newVars = [...variables];
    newVars[index] = updatedVariable;
    setVariables(newVars);
  };

  const addVariable = () => {
    setVariables([...variables, { name: "", distribution: "", parameters: {} }]);
  };

  const deleteVariable = (index) => {
    setVariables(vars => vars.length > 1 ? vars.filter((_, i) => i !== index) : vars);
  };

  const handleSubmit = () => {
    const varNames = variables.map((v) => v.name.trim());
    const formulaValid = varNames.every((v) => v && formula.includes(v));
    if (!formulaValid) {
      alert("Formula must reference all variable names correctly.");
      return;
    }
    onSubmit({ variables, formula, num_trials: numTrials });
  };

  
  return (
    <div className="p-6 space-y-6 ">
      {/* Variables section */}
      <div>
        {variables.length === 1 ? (
          // Center a single ParameterInput
          <div className="flex justify-center">
            <div className="w-full md:w-1/2 lg:w-1/3">
              <ParameterInput
                key={0}
                index={0}
                variable={variables[0]}
                onChange={handleVariableChange}
                onDelete={() => deleteVariable(0)}
                showDelete={false}
              />
            </div>
          </div>
        ) : (
          // Use grid for 2+
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {variables.map((variable, index) => (
              <ParameterInput
                key={index}
                index={index}
                variable={variable}
                onChange={handleVariableChange}
                onDelete={() => deleteVariable(index)}
                showDelete={variables.length > 1}
              />
            ))}
          </div>
        )}
        <div className="mt-8 print:hidden w-1/4 min-w-[200px] mx-auto">
          <Button onClick={addVariable}>ADD VARIABLE</Button>
        </div>
      </div>

      {/* Formula + run simulation section */}
      <div className="bg-white w-full md:w-1/2 lg:w-1/2 mx-auto border border-gray-700 shadow-md rounded-md p-6 space-y-4">
        <div>
          <label className="block text-xs text-left font-bold mb-1 tracking-wider text-gray-700 uppercase" htmlFor="formula-input">
            FORMULA
          </label>
          <textarea
            id="formula-input"
            placeholder="Enter formula (must use variables listed above)"
            className="block w-full mb-2 p-2 border border-gray-700 rounded focus:outline-none focus:border-gray-700 focus:ring-1 focus:ring-gray-700"
            value={formula}
            onChange={(e) => setFormula(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-xs text-left font-bold mb-1 tracking-wider text-gray-700 uppercase" htmlFor="num-trials-input">
            NUMBER OF TRIALS
          </label>
          <input
            id="num-trials-input"
            type="number"
            placeholder="Number of trials"
            className="block w-full mb-2 p-2 border border-gray-700 rounded focus:outline-none focus:border-gray-700 focus:ring-1 focus:ring-gray-700"
            value={numTrials}
            onChange={(e) => setNumTrials(parseInt(e.target.value, 10))}
          />
        </div>
        <div className="mt-8 print:hidden w-3/4 min-w-[200px] mx-auto">
          <Button onClick={handleSubmit}>RUN SIMULATION</Button>
        </div>
      </div>

      
    </div>
  );
};

export default ParameterForm;

