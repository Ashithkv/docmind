import { useRef, useState } from "react";
import { uploadDocuments } from "../services/api";

export default function DocumentUpload({ onUploadComplete }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  async function handleFiles(fileList) {
    const files = Array.from(fileList).filter((f) =>
      f.name.toLowerCase().endsWith(".pdf")
    );
    if (files.length === 0) {
      setError("Please select PDF files only.");
      return;
    }

    setError(null);
    setIsUploading(true);
    try {
      const result = await uploadDocuments(files);
      if (result.failed?.length) {
        const messages = result.failed
          .map((f) => `${f.filename}: ${f.error}`)
          .join(" | ");
        setError(messages);
      }
      onUploadComplete();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsUploading(false);
    }
  }

  function onDrop(e) {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.length) {
      handleFiles(e.dataTransfer.files);
    }
  }

  return (
    <div className="upload-section">
      <h2>Upload Documents</h2>
      <div
        className={`dropzone ${isDragging ? "dropzone-active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          multiple
          hidden
          onChange={(e) => e.target.files?.length && handleFiles(e.target.files)}
        />
        {isUploading ? (
          <p>Processing PDF(s)&hellip; this can take a moment.</p>
        ) : (
          <>
            <p className="dropzone-title">Drop PDF files here or click to browse</p>
            <p className="dropzone-subtitle">Multiple files supported</p>
          </>
        )}
      </div>
      {error && <div className="error-banner">{error}</div>}
    </div>
  );
}
