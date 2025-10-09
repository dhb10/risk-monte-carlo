import React, { useCallback, useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import Papa from 'papaparse';
import Button from './Button.jsx';


const RiskUpload = ({ isLoading, onSubmit, resetFileTrigger, clearResetFileTrigger, mode = "Scenarios" }) => {
  const REQUIRED_COLUMNS = mode === "Simulation"
    ? ['risk', 'scenario', 'variable', 'distribution', 'mean', 'std_dev', 'min', 'max', 'mode', 'formula', 'formula_equals']
    : ['sector', 'organization', 'risk_name', 'risk_definition'];
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');

  const onDrop = useCallback((acceptedFiles) => {
    const uploadedFile = acceptedFiles[0];
    if (!uploadedFile) {
      setError('Please upload a valid CSV file.');
      return;
    }
    if (!uploadedFile.name.endsWith('.csv')) {
      setError('Please upload a file with a .csv extension.');
      return;
    }
    Papa.parse(uploadedFile, {
      complete: ({ data, errors, meta }) => {
        if (errors.length > 0 || !Array.isArray(data) || data.length === 0) {
          setError('There was an error parsing the CSV file.');
          return;
        }
        // PapaParse header: true puts headers into meta.fields
        // Let’s force header: true for easier handling!
        if (!meta.fields || meta.fields.length !== REQUIRED_COLUMNS.length) {
          setError(`CSV must have exactly these columns: ${REQUIRED_COLUMNS.join(', ')}.`);
          return;
        }
        const normalizedHeaders = meta.fields.map(col => col.trim().toLowerCase());
        if (
          !REQUIRED_COLUMNS.every((col, idx) => normalizedHeaders[idx] === col)
        ) {
          setError(`Column headers must be exactly: ${REQUIRED_COLUMNS.join(', ')} (in this order).`);
          return;
        }
        setFile(uploadedFile);
        setError('');
      },
      header: true, //force headers
      skipEmptyLines: true,
    });
  }, []);

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 1,
  });

  const handleFileSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      alert('Please upload a CSV file before submitting!');
      return;
    }
    const formData = new FormData();
    formData.append('file', file);
    await onSubmit(formData);
  };

  useEffect(() => {
    if (resetFileTrigger) {
      setFile(null);
      setError('');
      clearResetFileTrigger();
    }
  }, [resetFileTrigger, clearResetFileTrigger]);

  return (
    <div className="text-center text-black">
      <div
        {...getRootProps()}
        className="p-4 border-2 max-w-lg mx-auto  border-dashed border-gray-300 rounded-md bg-gray-100 hover:border-black cursor-pointer mt-6 print:hidden"
      >
        <input {...getInputProps()} />
        {file ? (
          <p className="text-green-600">{file.name}</p>
        ) : (
          <p>Drag and drop a CSV file here, or click to upload</p>
        )}
      </div>
      {error && <p className="text-red-500 mt-2">{error}</p>}
      <div className="mt-8 print:hidden w-1/4 min-w-[200px] mx-auto">
        <Button onClick={handleFileSubmit} isSelected={false} isDisabled={isLoading}>
          SUBMIT
        </Button>
      </div>
    </div>
  );
};

export default RiskUpload;