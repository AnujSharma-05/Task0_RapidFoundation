// Standalone API Endpoint Test Script
// To run: node test_api.js

const BACKEND_URL = 'http://127.0.0.1:8000';

async function runTests() {
  console.log('[START] Starting API Integration Diagnostics...');
  
  // Test 1: Ping
  try {
    const start = Date.now();
    const res = await fetch(`${BACKEND_URL}/ping`);
    const data = await res.json();
    console.log(`[PASS] [1/4] GET /ping - Success (${Date.now() - start}ms)`);
    console.log('      Response:', data);
  } catch (err) {
    console.error('[FAIL] [1/4] GET /ping - Failed');
    console.error('      Error:', err.message);
    return;
  }

  // Test 2: Get Documents
  let documents = [];
  try {
    const start = Date.now();
    const res = await fetch(`${BACKEND_URL}/documents`);
    documents = await res.json();
    console.log(`[PASS] [2/4] GET /documents - Success (${Date.now() - start}ms)`);
    console.log(`      Found ${documents.length} document(s)`);
  } catch (err) {
    console.error('[FAIL] [2/4] GET /documents - Failed');
    console.error('      Error:', err.message);
  }

  // Test 3: Debug DB Status
  try {
    const start = Date.now();
    const res = await fetch(`${BACKEND_URL}/debug/db`);
    const data = await res.json();
    console.log(`[PASS] [3/4] GET /debug/db - Success (${Date.now() - start}ms)`);
    console.log('      Status:', data);
  } catch (err) {
    console.error('[FAIL] [3/4] GET /debug/db - Failed');
    console.error('      Error:', err.message);
  }

  // Test 4: Chat Ingestion / Generation test
  try {
    const start = Date.now();
    const res = await fetch(`${BACKEND_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: 'Hi, testing RAG capability',
        document_id: null,
        top_k: 3
      })
    });
    const data = await res.json();
    console.log(`[PASS] [4/4] POST /chat - Success (${Date.now() - start}ms)`);
    console.log('      Grounded Answer:', data.answer);
    console.log(`      Citations Returned: ${data.citations ? data.citations.length : 0}`);
  } catch (err) {
    console.error('[FAIL] [4/4] POST /chat - Failed');
    console.error('      Error:', err.message);
  }

  console.log('\n[DONE] Diagnostics Completed!');
}

runTests();
