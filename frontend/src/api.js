const API_BASE_URL = 'http://127.0.0.1:8000';

/**
 * Fetch all uploaded documents from the server.
 */
export async function fetchDocuments() {
  const response = await fetch(`${API_BASE_URL}/documents`);
  if (!response.ok) {
    throw new Error('Failed to fetch documents');
  }
  return response.json();
}

/**
 * Upload a PDF file to the backend.
 * @param {File} file 
 */
export async function uploadDocument(file, category = null) {
  const formData = new FormData();
  formData.append('file', file);
  if (category) {
    formData.append('category', category);
  }
  
  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to upload document');
  }
  return response.json();
}

/**
 * Delete a specific document by its ID.
 * @param {number} id 
 */
export async function deleteDocument(id) {
  const response = await fetch(`${API_BASE_URL}/documents/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete document');
  }
  return response.json();
}

/**
 * Reset the entire system (deletes all documents, chunks, and Milvus collection).
 */
export async function resetSystem() {
  const response = await fetch(`${API_BASE_URL}/documents`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to reset system');
  }
  return response.json();
}

/**
 * Send a chat query to the model.
 * @param {string} question 
 * @param {number|null} documentId 
 * @param {number} topK 
 */
export async function askQuestion(question, documentId = null, category = null, topK = 5) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      document_id: documentId ? parseInt(documentId, 10) : null,
      category: category || null,
      top_k: parseInt(topK, 10),
    }),
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to generate answer');
  }
  return response.json();
}

/**
 * Trigger backend garbage collection and zombie process termination.
 */
export async function cleanSystem() {
  const response = await fetch(`${API_BASE_URL}/clean-system`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to clean system processes');
  }
  return response.json();
}
