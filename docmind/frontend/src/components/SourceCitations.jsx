export default function SourceCitations({ sources }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="sources">
      <h4>Sources</h4>
      <ul className="source-list">
        {sources.map((source, idx) => (
          <li key={idx} className="source-item">
            <div className="source-header">
              <span className="source-doc">
                {source.document_name} — Page {source.page}
              </span>
              <span className="source-score">
                {Math.round(source.similarity_score * 100)}% match
              </span>
            </div>
            <p className="source-text">{source.text}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
