import React, { useState, useEffect } from 'react';
import { addMonths, subMonths, isSameDay, format } from 'date-fns';
import { useGoogleCalendar } from './hooks/useGoogleCalendar';
import { useGoogleAuth } from './hooks/useGoogleAuth';
import { CalendarGrid } from './components/CalendarGrid';
import { CalendarHeader } from './components/CalendarHeader';
import { EventDetails } from './components/EventDetails';
import { AuthButton } from './components/AuthButton';
import { CalendarDays, Sun, CalendarCheck2, MessageCircle, X } from 'lucide-react';
import { Settings } from './components/Settings';
import { Chatbot } from './components/Chatbot';
import { QuickEventModal } from './components/QuickEventModal';

function App() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [showChatbot, setShowChatbot] = useState(false);
  const [showQuickEvent, setShowQuickEvent] = useState(false);
  
  const { isSignedIn, loading: authLoading, error: authError, signIn, signOut, retry } = useGoogleAuth();
  const {
    getEventsForMonth,
    ensureEvents,
    refreshEvents,
    loading: eventsLoading,
    error,
  } = useGoogleCalendar();

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  useEffect(() => {
    if (isSignedIn) {
      ensureEvents(year, month);
    }
    // eslint-disable-next-line
  }, [year, month, isSignedIn]);

  const handlePrevMonth = () => {
    setCurrentDate(prev => subMonths(prev, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(prev => addMonths(prev, 1));
  };

  const handleToday = () => {
    setCurrentDate(new Date());
  };

  const handleRefresh = async () => {
    await refreshEvents(year, month);
  };

  const handleQuickEventClose = () => {
    setShowQuickEvent(false);
  };

  const handleEventsCreated = () => {
    // Refresh the calendar events after new events are created
    handleRefresh();
  };

  const handleDateSelect = (date: Date) => {
    setSelectedDate(date);
  };

  const events = getEventsForMonth(year, month);

  // Metrics calculations
  const daysWithEvents = Array.from(new Set(events.map(event => {
    return event.start.dateTime
      ? new Date(event.start.dateTime).toDateString()
      : new Date(event.start.date + 'T00:00:00').toDateString();
  })));
  const allDayEvents = events.filter(event => !event.start.dateTime).length;

  const getSelectedDateEvents = () => {
    if (!selectedDate) return [];
    return events.filter(event => {
      const eventDate = event.start.dateTime 
        ? new Date(event.start.dateTime)
        : new Date(event.start.date + 'T00:00:00');
      return isSameDay(eventDate, selectedDate);
    });
  };

  // Google Calendar Sign-In Button
  if (!isSignedIn) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <div className="bg-white rounded-xl shadow-xl p-8 flex flex-col items-center">
          <h1 className="text-2xl font-bold mb-6 text-gray-900">Sign in to Google Calendar</h1>
          <AuthButton
            isSignedIn={isSignedIn}
            loading={authLoading}
            error={authError}
            onSignIn={signIn}
            onSignOut={signOut}
            onRetry={retry}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col lg:flex-row gap-8">
        {/* Calendar Section */}
        <div className="flex-1">
          {/* Metrics Bar */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="flex items-center bg-blue-100 rounded-xl shadow border border-blue-200 p-5">
              <CalendarCheck2 size={32} className="text-blue-500 mr-4" />
              <div>
                <div className="text-sm text-blue-700 font-medium">Events this month</div>
                <div className="text-2xl font-bold text-blue-800">{events.length}</div>
              </div>
            </div>
            <div className="flex items-center bg-green-100 rounded-xl shadow border border-green-200 p-5">
              <CalendarDays size={32} className="text-green-500 mr-4" />
              <div>
                <div className="text-sm text-green-700 font-medium">Days with events</div>
                <div className="text-2xl font-bold text-green-800">{daysWithEvents.length}</div>
              </div>
            </div>
            <div className="flex items-center bg-purple-100 rounded-xl shadow border border-purple-200 p-5">
              <Sun size={32} className="text-purple-500 mr-4" />
              <div>
                <div className="text-sm text-purple-700 font-medium">All-day events</div>
                <div className="text-2xl font-bold text-purple-800">{allDayEvents}</div>
              </div>
            </div>
          </div>
          {/* Header */}
          <CalendarHeader
            currentDate={currentDate}
            onPrevMonth={handlePrevMonth}
            onNextMonth={handleNextMonth}
            onToday={handleToday}
            onRefresh={handleRefresh}
            onSettings={() => setShowSettings(true)}
            onSignOut={signOut}
            onQuickEvent={() => setShowQuickEvent(true)}
            refreshing={eventsLoading}
          />
          {/* Calendar Grid */}
          {eventsLoading ? (
            <div>Loading...</div>
          ) : error ? (
            <div className="text-red-600">{error}</div>
          ) : (
            <CalendarGrid
              currentDate={currentDate}
              events={events}
              onDateSelect={handleDateSelect}
              selectedDate={selectedDate}
            />
          )}
        </div>
        {/* Sidebar Event Details */}
        {selectedDate && (
          <div className="w-full lg:w-[350px] xl:w-[400px] flex-shrink-0">
            <EventDetails
              events={getSelectedDateEvents()}
              selectedDate={selectedDate}
              onClose={() => setSelectedDate(null)}
            />
          </div>
        )}
        {/* Settings Modal */}
        {showSettings && (
          <Settings
            currentClientId={null}
            onClientIdUpdate={() => {}}
            onClose={() => setShowSettings(false)}
          />
        )}
        {/* Chatbot Floating Button and Modal */}
        <button
          onClick={() => setShowChatbot(true)}
          className="fixed bottom-6 right-6 z-50 bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg flex items-center justify-center"
          title="Chat with your calendar assistant"
        >
          <MessageCircle size={28} />
        </button>
        {showChatbot && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
            <div className="relative w-full max-w-4xl h-full max-h-[90vh] mx-4 flex flex-col bg-transparent">
              <button
                onClick={() => setShowChatbot(false)}
                className="absolute -top-2 -right-2 z-10 bg-white hover:bg-gray-100 text-gray-600 hover:text-gray-800 p-2 rounded-full shadow-lg transition-colors"
                aria-label="Close chatbot"
              >
                <X size={20} />
              </button>
              <div className="flex-1 flex items-center justify-center">
                <Chatbot userName="User" calendarEvents={events} />
              </div>
            </div>
          </div>
        )}
        
        {/* Quick Event Modal */}
        <QuickEventModal
          isOpen={showQuickEvent}
          onClose={handleQuickEventClose}
          onEventsCreated={handleEventsCreated}
        />
      </div>
    </div>
  );
}

export default App;