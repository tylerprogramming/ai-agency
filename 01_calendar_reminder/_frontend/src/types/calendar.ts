export interface CalendarEvent {
  id: string;
  summary: string;
  start: {
    dateTime?: string;
    date?: string;
  };
  end: {
    dateTime?: string;
    date?: string;
  };
  description?: string;
  location?: string;
  colorId?: string;
  htmlLink?: string; // Added to match Google Calendar API
}

export interface AuthState {
  isSignedIn: boolean;
  user: any | null;
  loading: boolean;
}