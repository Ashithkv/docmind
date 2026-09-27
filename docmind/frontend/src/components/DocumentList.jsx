import { useState } from "react";
import { deleteDocument } from "../services/api";

function statusLabel(status) {
  if (status === "ready") return { text: "Ready", cls: "status-ready" };
  if (status === "processing") return { text: "Processing", cls: "status-processing" };
  return { text: "Failed", cls: "status-failed" };
}

export default function DocumentList({ documents, onChange }) {
  const [deletingId, setDeletingId] = useState(null);

  async function handleDelete(documentId) {
    setDeletingId(documentId);
    try {
      await deleteDocument(documentId);
      onChange();
    } catch (err) {
      alert(`Failed to delete document: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="document-list-section">
      <h2>Documents ({documents.length})</h2>
      {documents.length === 0 ? (
        <p className="empty-hint">No documents uploaded yet.</p>
      ) : (
        <ul className="document-list">
          {documents.map((doc) => {
            const status = statusLabel(doc.status);
            return (
              <li key={doc.document_id} className="document-item">
                <div className="document-info">
                  <span className="document-name" title={doc.filename}>
                    {doc.filename}
                  </span>
                  <span className={`status-badge ${status.cls}`}>{status.text}</span>
                </div>
                <div className="document-meta">
                  {doc.status === "ready" && (
                    <span>
                      {doc.num_pages} pages &middot; {doc.num_chunks} chunks
                    </span>
                  )}
                  {doc.status === "failed" && (
                    <span className="document-error">{doc.error}</span>
                  )}
                </div>
                <button
                  className="delete-btn"
                  onClick={() => handleDelete(doc.document_id)}
                  disabled={deletingId === doc.document_id}
                >
                  {deletingId === doc.document_id ? "Deleting…" : "Delete"}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
