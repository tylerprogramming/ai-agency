import { useState, useRef } from 'react';
import { CalendarEvent } from '../types/calendar';

interface CalendarCache {
  [key: string]: CalendarEvent[];
}

export const useGoogleCalendar = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cache = useRef<CalendarCache>({});

  const getCacheKey = (year: number, month: number) => `${year}-${String(month + 1).padStart(2, '0')}`;

  const getEventsForMonth = (year: number, month: number): CalendarEvent[] => {
    const key = getCacheKey(year, month);
    return cache.current[key] || [];
  };

  const fetchEvents = async (year: number, month: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/calendar/events');
      if (!response.ok) throw new Error('Failed to fetch events');
      const events = await response.json();
      const key = getCacheKey(year, month);
      cache.current[key] = events;
    } catch (error) {
      setError('Failed to load calendar events');
    } finally {
      setLoading(false);
    }
  };

  const refreshEvents = (year: number, month: number) => {
    // Always fetch and overwrite cache
    return fetchEvents(year, month);
  };

  const ensureEvents = async (year: number, month: number) => {
    const key = getCacheKey(year, month);
    if (!cache.current[key]) {
      await fetchEvents(year, month);
    }
  };

  return {
    getEventsForMonth,
    ensureEvents,
    refreshEvents,
    loading,
    error,
  };
};