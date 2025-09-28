import React from 'react';
import Button from './Button';

const ResultsButtons = ({
    response,
    handleReset,
    handleDownload,
    handleDownloadPdf,
    isLoading,
}) => {
    if (isLoading || !response || response.length === 0) return null;
    return (
        <div className="mb-8 flex flex-wrap gap-4 w-full justify-center print:hidden">
            <Button onClick={handleReset} isDisabled={isLoading}>
                RESET
            </Button>
            <Button onClick={handleDownload} isDisabled={isLoading}>
                DOWNLOAD CSV
            </Button>
            <Button onClick={handleDownloadPdf} isDisabled={isLoading}>
                DOWNLOAD PDF
            </Button>
        </div>
    );
};

export default ResultsButtons;