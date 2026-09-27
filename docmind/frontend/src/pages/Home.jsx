import { useCallback, useEffect, useState } from "react";
import DocumentUpload from "../components/DocumentUpload.jsx";
import DocumentList from "../components/DocumentList.jsx";
import ChatWindow from "../components/ChatWindow.jsx";
import { listDocuments } from "../services/api";

export default function Home() {
  const [documents, setDocuments] = useState([]);
  const [loadError, setLoadError] = useState(null);

  const refreshDocuments = useCallback(async () => {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
      setLoadError(null);
    } catch (err) {
      setLoadError(err.message);
    }
  }, []);

  useEffect(() => {
    refreshDocuments();
  }, [refreshDocuments]);

  const hasReadyDocuments = documents.some((d) => d.status === "ready");

  return (
    <div className="home-layout">
      <header className="app-header">
        <h1>DocMind</h1>
        <p className="app-subtitle">Ask questions about your PDF documents, with citations.</p>
      </header>

      {loadError && <div className="error-banner">{loadError}</div>}

      <div className="main-grid">
        <div className="left-column">
          <DocumentUpload onUploadComplete={refreshDocuments} />
          <DocumentList documents={documents} onChange={refreshDocuments} />
        </div>
        <div className="right-column">
          <ChatWindow hasDocuments={hasReadyDocuments} />
        </div>
      </div>
    </div>
  );
}
