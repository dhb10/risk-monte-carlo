import React from 'react';
import Button from './Button';

const ResultsButtons = ({
    response,
    handleReset,
    handleDownload,
    handleDownloadPdf,
    isLoading,
    selectedMode,
    manualMode,
}) => {
    if (isLoading || !response || response.length === 0) return null;

    if (selectedMode === "Scenarios") {
        // All three buttons
        return (
            <div className="mb-8 flex flex-wrap gap-4 w-full justify-center print:hidden">
                <Button onClick={handleReset} isDisabled={isLoading} className="max-w-[200px]">
                    RESET
                </Button>
                <Button onClick={handleDownload} isDisabled={isLoading} className="max-w-[200px]">
                    DOWNLOAD CSV
                </Button>
                <Button onClick={handleDownloadPdf} isDisabled={isLoading} className="max-w-[200px]">
                    DOWNLOAD PDF
                </Button>
            </div>
        );
    } else if (selectedMode === "Simulation") {
        // Only reset + PDF
        return (
            <div className="mb-8 flex flex-wrap gap-4 w-full justify-center print:hidden">
                <Button onClick={handleReset} isDisabled={isLoading} className="max-w-[200px]">
                    RESET
                </Button>
                {manualMode ? (
                    <Button onClick={() => window.print()} isDisabled={isLoading} className="max-w-[200px]">
                        PRINT SCREEN
                    </Button>
                ) : (
                    <Button onClick={handleDownloadPdf} isDisabled={isLoading} className="max-w-[200px]">
                        DOWNLOAD PDF
                    </Button>
                )}
            </div>
        );
    } else {
        // No controls
        return null;
    }
};

export default ResultsButtons;