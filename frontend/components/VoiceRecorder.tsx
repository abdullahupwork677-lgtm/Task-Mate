'use client';

import { useState, useRef, useEffect } from 'react';
import { getToken } from '@/lib/auth';

interface VoiceRecorderProps {
  onTranscription: (text: string) => void;
  disabled?: boolean;
}

export function VoiceRecorder({ onTranscription, disabled }: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const recordingStartTimeRef = useRef<number>(0);

  // Minimum recording duration in milliseconds (0.5 seconds)
  const MIN_RECORDING_DURATION = 500;

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      setError(null);

      // Check for secure context (HTTPS or localhost) — getUserMedia requires it
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        if (!isLocalhost && window.location.protocol !== 'https:') {
          setError('Microphone requires HTTPS. Please use https://todo.139.59.195.161.nip.io');
        } else {
          setError('Microphone not supported in this browser.');
        }
        return;
      }

      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // Collect audio data
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // Handle recording stop
      mediaRecorder.onstop = async () => {
        // Check recording duration
        const recordingDuration = Date.now() - recordingStartTimeRef.current;

        if (recordingDuration < MIN_RECORDING_DURATION) {
          setError(`Recording too short. Please hold for at least 0.5 seconds.`);
          setIsProcessing(false);

          // Cleanup stream
          if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
          }
          return;
        }

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

        // Validate audio blob size (should be at least a few KB)
        if (audioBlob.size < 1000) {
          setError('Recording is too short or empty. Please try again.');
          setIsProcessing(false);

          // Cleanup stream
          if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
          }
          return;
        }

        await transcribeAudio(audioBlob);

        // Cleanup stream
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
      };

      // Start recording
      recordingStartTimeRef.current = Date.now();
      mediaRecorder.start();
      setIsRecording(true);

    } catch (err: any) {
      console.error('Failed to start recording:', err);
      setError(err.message || 'Failed to access microphone');
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const transcribeAudio = async (audioBlob: Blob) => {
    setIsProcessing(true);
    setError(null);

    try {
      // Get authentication token
      const token = getToken();
      if (!token) {
        throw new Error('Not authenticated');
      }

      // Create FormData
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');

      // Send to backend via proxy (now supports FormData)
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '/api/proxy';

      // Add timeout to prevent infinite loading (30 seconds max)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);

      const response = await fetch(`${apiUrl}/api/voice/transcribe`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json();
        // Handle specific error cases
        if (error.detail && error.detail.includes('too short')) {
          throw new Error('Recording too short. Please hold the button longer (at least 0.5 seconds).');
        }
        throw new Error(error.detail || 'Transcription failed');
      }

      const data = await response.json();

      // Pass transcribed text to parent
      if (data.text) {
        onTranscription(data.text);
      }

    } catch (err: any) {
      console.error('Transcription failed:', err);
      // Handle abort error specifically
      if (err.name === 'AbortError') {
        setError('Transcription timeout - please try again with shorter audio');
      } else {
        setError(err.message || 'Failed to transcribe audio');
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleMouseDown = () => {
    if (!disabled && !isProcessing) {
      startRecording();
    }
  };

  const handleMouseUp = () => {
    if (isRecording) {
      stopRecording();
    }
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    e.preventDefault();
    if (!disabled && !isProcessing) {
      startRecording();
    }
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    e.preventDefault();
    if (isRecording) {
      stopRecording();
    }
  };

  return (
    <div className="relative">
      <button
        type="button"
        disabled={disabled || isProcessing}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        className={`flex-shrink-0 w-11 h-11 sm:w-12 sm:h-12 rounded-full flex items-center justify-center transition-all duration-200 shadow-lg ${
          isRecording
            ? 'bg-red-500 animate-pulse scale-110'
            : isProcessing
            ? 'bg-blue-400'
            : 'bg-gradient-to-br from-purple-500 to-pink-600 hover:shadow-xl hover:scale-105 active:scale-95'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        aria-label={isRecording ? 'Recording... Release to stop' : isProcessing ? 'Processing...' : 'Hold to speak (min 0.5s)'}
        title={isRecording ? 'Recording... Release to stop' : isProcessing ? 'Transcribing...' : 'Hold to speak (minimum 0.5 seconds)'}
      >
        {isProcessing ? (
          <svg
            className="animate-spin h-5 w-5 text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        ) : isRecording ? (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="currentColor"
            viewBox="0 0 24 24"
            className="w-6 h-6 text-white"
          >
            <rect x="6" y="4" width="4" height="16" rx="2" />
            <rect x="14" y="4" width="4" height="16" rx="2" />
          </svg>
        ) : (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
            className="w-6 h-6 text-white"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z"
            />
          </svg>
        )}
      </button>

      {/* Recording indicator */}
      {isRecording && (
        <div className="absolute -top-1 -right-1">
          <div className="w-4 h-4 bg-red-500 rounded-full animate-ping" />
          <div className="w-4 h-4 bg-red-500 rounded-full absolute top-0 right-0" />
        </div>
      )}

      {/* Error tooltip */}
      {error && (
        <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 w-48 bg-red-500 text-white text-xs rounded-lg py-2 px-3 shadow-lg">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-2 font-bold"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}
