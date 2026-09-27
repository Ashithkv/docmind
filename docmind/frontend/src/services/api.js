import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE_URL,
});

/**
 * Extract a human-readable error message from an axios error, falling back
 * gracefully if the backend didn't return a structured `detail` field.
 */
function errorMessage(error) {
  if (error.response?.data?.detail) return error.response.data.detail;
  if (error.message) return error.message;
  return "Something went wrong. Please try again.";
}

export async function uploadDocuments(files) {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  try {
    const res = await client.post("/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  } catch (error) {
    throw new Error(errorMessage(error));
  }
}

export async function listDocuments() {
  try {
    const res = await client.get("/documents");
    return res.data.documents;
  } catch (error) {
    throw new Error(errorMessage(error));
  }
}

export async function deleteDocument(documentId) {
  try {
    const res = await client.delete(`/documents/${documentId}`);
    return res.data;
  } catch (error) {
    throw new Error(errorMessage(error));
  }
}

export async function askQuestion(question, documentIds = null) {
  try {
    const res = await client.post("/chat", {
      question,
      document_ids: documentIds,
    });
    return res.data;
  } catch (error) {
    throw new Error(errorMessage(error));
  }
}
