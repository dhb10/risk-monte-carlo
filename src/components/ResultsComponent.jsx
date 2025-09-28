import React from "react";

// Helper: escape HTML for footnotes in case of special chars (kept for future use)
function escapeHtml(unsafe) {
  return unsafe
    .replace(/[&<"']/g, function (m) {
      switch (m) {
        case "&": return "&amp;";
        case "<": return "&lt;";
        case '"': return "&quot;";
        case "'": return "&#039;";
        default: return m;
      }
    });
}

const ResultsComponent = ({ response }) => {
  // Defensive: If there's truly nothing or wrong structure, early exit.
  if (!Array.isArray(response)) {
    return <div className="text-red-500">No results to display.</div>;
  }

  // Global footnote assignment
  let contentToIndex = {};
  let contents = [];
  let nextFootnote = 1;

  function getContentIndex(content) {
    if (contentToIndex[content] !== undefined) {
      return contentToIndex[content];
    }
    contentToIndex[content] = nextFootnote;
    contents.push(content);
    return nextFootnote++;
  }

  return (
    <div className="w-full mx-auto px-4 text-left">
      {response.map((risk, riskIdx) => {
        // Defensive: if results block missing
        const docs = Array.isArray(risk?.results?.scenario_documents)
          ? risk.results.scenario_documents
          : [];
        return (
          <div key={riskIdx} className="mb-8">
            <h3 className="text-lg font-bold mb-1">{risk.risk_name}</h3>
            {risk.risk_definition && (
              <div className="text-lg mb-2 text-gray-600">{risk.risk_definition}</div>
            )}

            {docs.length === 0 && (
              <div className="text-gray-600 mb-4 text-md">No scenario documents found.</div>
            )}

            {docs.map((source, srcIdx) => {
              const contentFootnoteNum = getContentIndex(source.content);

              return (
                <div key={srcIdx} className="mt-4 mb-8 pl-2">
                  <div>
                    LINK:<br />
                    <a
                      href={source.url}
                      className="font-semibold text-blue-700 underline"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {source.title}
                    </a>
                    <sup className="ml-1 text-xs">{contentFootnoteNum}</sup>
                  </div>
                  <div className="text-lg text-gray-700 mt-4 mb-4">
                    Query: {source.search_query}
                  </div>
                  <ul className="list-disc list-outside ml-4 text-gray-600 text-lg">
                    {(source.scenarios || []).map((sc, scIdx) => (
                      <li key={scIdx} className="mb-1">
                        {sc.scenario}
                        <ul className="list-[circle] list-outside ml-4 text-gray-600 text-s">
                          <li>{sc.reasoning}</li>
                        </ul>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
            {riskIdx !== response.length - 1 && <hr />}
          </div>
        );
      })}

      {/* Footnotes section */}
      <div className="mt-10 border-t pt-6 w-full mx-auto px-4">
        <h2 className="text-md font-semibold mb-3">Source content</h2>
        <ol className="list-decimal list-outside text-md text-gray-900">
          {contents.map((ct, i) => (
            <li key={i} className="mb-3 ">
              {/* whitespace-pre-line */}
              {ct}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
};

export default ResultsComponent;