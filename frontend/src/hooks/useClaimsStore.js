'use client';
import { useState, useCallback } from 'react';
import { processClaim, processClaimsBatch } from '@/lib/api';

/**
 * Central state store for claims processing.
 * Keeps a history of all processed claims in the session.
 */
export function useClaimsStore() {
  const [claims, setClaims] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);

  const addClaim = useCallback((result) => {
    setClaims((prev) => [result, ...prev]);
  }, []);

  const submitSingle = useCallback(async (file) => {
    setProcessing(true);
    setError(null);
    setUploadProgress(0);
    try {
      const result = await processClaim(file, setUploadProgress);
      addClaim({ ...result, _filename: file.name, _submittedAt: new Date().toISOString() });
      return result;
    } catch (err) {
      setError(err.detail || err.message || 'Processing failed');
      return null;
    } finally {
      setProcessing(false);
      setUploadProgress(0);
    }
  }, [addClaim]);

  const submitBatch = useCallback(async (files) => {
    setProcessing(true);
    setError(null);
    try {
      const result = await processClaimsBatch(files);
      result.items.forEach((item) => {
        if (item.status === 'success' && item.response) {
          addClaim({ ...item.response, _filename: item.filename, _submittedAt: new Date().toISOString() });
        }
      });
      return result;
    } catch (err) {
      setError(err.detail || err.message || 'Batch processing failed');
      return null;
    } finally {
      setProcessing(false);
    }
  }, [addClaim]);

  const clearError = useCallback(() => setError(null), []);
  const clearClaims = useCallback(() => setClaims([]), []);

  return {
    claims,
    processing,
    uploadProgress,
    error,
    submitSingle,
    submitBatch,
    clearError,
    clearClaims,
  };
}