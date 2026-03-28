'use client';

import { useState, useRef, useEffect } from 'react';
import { getToken } from '@/lib/auth';
import { getApiBaseUrl } from '@/lib/api';

interface TextToSpeechProps {
  text: string;
  voice?: string;
  speed?: number;
}

export function TextToSpeech({ text, voice = 'nova', speed = 1.0 }: TextToSpeechProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
      }
    };
  }, []);

  const playAudio = async () => {
    if (isPlaying) {
      // Stop current playback
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
      setIsPlaying(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Validate text content
      if (!text || text.trim().length === 0) {
        throw new Error('No text to convert to speech');
      }

      // Fetch audio from backend via proxy (now supports binary audio)
      const token = getToken();
      if (!token) {
        throw new Error('Not authenticated');
      }

      // Must match apiFetch (chat): same-origin / env URL — not /api/proxy alone (proxy BACKEND_URL often wrong in K8s)
      const apiUrl = getApiBaseUrl().replace(/\/$/, '');
      const response = await fetch(`${apiUrl}/api/voice/text-to-speech`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          text,
          voice,
          speed
        }),
      });

      if (!response.ok) {
        const ct = response.headers.get('content-type') || '';
        let detail = `TTS failed (${response.status})`;
        try {
          if (ct.includes('application/json')) {
            const error = await response.json();
            detail = error.detail || error.message || detail;
          } else {
            const text = await response.text();
            if (text) detail = text.slice(0, 200);
          }
        } catch {
          /* keep detail */
        }
        throw new Error(detail);
      }

      // Get audio blob
      const audioBlob = await response.blob();

      // Create audio URL
      const audioUrl = URL.createObjectURL(audioBlob);
      audioUrlRef.current = audioUrl;

      // Create and play audio element
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onplay = () => {
        setIsPlaying(true);
        setIsLoading(false);
      };

      audio.onended = () => {
        setIsPlaying(false);
        // Cleanup
        URL.revokeObjectURL(audioUrl);
        audioUrlRef.current = null;
      };

      audio.onerror = () => {
        setError('Failed to play audio');
        setIsPlaying(false);
        setIsLoading(false);
      };

      await audio.play();

    } catch (err: any) {
      console.error('TTS failed:', err);
      setError(err.message || 'Failed to generate speech');
      setIsLoading(false);
      setIsPlaying(false);
    }
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={playAudio}
        disabled={isLoading || !text}
        className={`p-2 rounded-full transition-all duration-200 ${
          isPlaying
            ? 'bg-blue-500 text-white animate-pulse'
            : 'hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300'
        } ${isLoading || !text ? 'opacity-50 cursor-not-allowed' : ''}`}
        aria-label={isPlaying ? 'Stop playback' : 'Play audio'}
        title={isPlaying ? 'Stop playback' : 'Listen to response'}
      >
        {isLoading ? (
          <svg
            className="animate-spin h-4 w-4"
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
        ) : isPlaying ? (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="currentColor"
            viewBox="0 0 24 24"
            className="w-4 h-4"
          >
            <rect x="6" y="4" width="4" height="16" rx="1" />
            <rect x="14" y="4" width="4" height="16" rx="1" />
          </svg>
        ) : (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
            className="w-4 h-4"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z"
            />
          </svg>
        )}
      </button>

      {/* Error tooltip */}
      {error && (
        <div className="absolute bottom-full mb-2 right-0 w-48 bg-red-500 text-white text-xs rounded-lg py-2 px-3 shadow-lg z-10">
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
