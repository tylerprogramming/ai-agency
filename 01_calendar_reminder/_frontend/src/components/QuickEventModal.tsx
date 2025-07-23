import React, { useState } from 'react';
import { X, Plus, Loader2, Calendar, Sparkles, AlertCircle, CheckCircle } from 'lucide-react';

interface QuickEventModalProps {
  isOpen: boolean;
  onClose: () => void;
  onEventsCreated: () => void; // Callback to refresh calendar
}

interface CreatedEvent {
  title: string;
  start: string;
  end: string;
  result: string;
}

interface FailedEvent {
  event: any;
  error: string;
}

export const QuickEventModal: React.FC<QuickEventModalProps> = ({
  isOpen,
  onClose,
  onEventsCreated,
}) => {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<{
    success: boolean;
    message: string;
    events_created: number;
    events_failed: number;
    created_events: CreatedEvent[];
    failed_events: FailedEvent[];
  } | null>(null);

  const openaiKey = typeof window !== 'undefined' ? localStorage.getItem('openai_api_key') : null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || !openaiKey) return;

    setLoading(true);
    setResults(null);

    try {
      const response = await fetch('http://localhost:8000/api/parse-text-to-events', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text.trim(),
          openai_api_key: openaiKey,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setResults({
          success: true,
          message: data.message,
          events_created: data.events_created,
          events_failed: data.events_failed,
          created_events: data.created_events || [],
          failed_events: data.failed_events || [],
        });

        if (data.events_created > 0) {
          onEventsCreated(); // Refresh the calendar
        }
      } else {
        setResults({
          success: false,
          message: data.detail || 'Failed to create events',
          events_created: 0,
          events_failed: 0,
          created_events: [],
          failed_events: [],
        });
      }
    } catch (error) {
      setResults({
        success: false,
        message: `Error: ${error}`,
        events_created: 0,
        events_failed: 0,
        created_events: [],
        failed_events: [],
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setText('');
    setResults(null);
    onClose();
  };

  const formatDateTime = (dateTimeStr: string) => {
    try {
      return new Date(dateTimeStr).toLocaleString();
    } catch {
      return dateTimeStr;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl mx-4 bg-white rounded-xl shadow-xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-full">
              <Sparkles size={20} className="text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Quick Event Creator</h2>
              <p className="text-sm text-gray-600">Paste text and AI will create calendar events</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X size={20} className="text-gray-600" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {!results ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Input Section */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Paste your text here
                </label>
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Example: Meeting with John tomorrow at 2pm for 1 hour about project discussion in conference room A"
                  className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none text-sm"
                  disabled={loading}
                />
                <p className="mt-2 text-xs text-gray-500">
                  AI will parse dates, times, locations, and other event details from your text
                </p>
              </div>

              {/* Examples */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Example formats:</h4>
                <div className="text-xs text-gray-600 space-y-1">
                  <p>• "Team standup tomorrow at 9am for 30 minutes"</p>
                  <p>• "Lunch with Sarah on Friday at 12:30pm at Joe's Cafe"</p>
                  <p>• "Project review meeting next Tuesday from 2-4pm with john@company.com"</p>
                  <p>• "Dentist appointment July 25th at 10am"</p>
                </div>
              </div>

              {!openaiKey && (
                <div className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
                  <AlertCircle size={16} />
                  <span className="text-sm">Please add your OpenAI API key in Settings to use this feature.</span>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading || !text.trim() || !openaiKey}
                className="w-full flex items-center justify-center space-x-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white py-3 px-4 rounded-lg font-medium transition-colors"
              >
                {loading ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    <span>Creating Events...</span>
                  </>
                ) : (
                  <>
                    <Plus size={18} />
                    <span>Create Events</span>
                  </>
                )}
              </button>
            </form>
          ) : (
            /* Results Section */
            <div className="space-y-4">
              {/* Summary */}
              <div className={`flex items-center space-x-3 p-4 rounded-lg ${
                results.success && results.events_created > 0
                  ? 'bg-green-50 border border-green-200'
                  : results.success
                  ? 'bg-yellow-50 border border-yellow-200'
                  : 'bg-red-50 border border-red-200'
              }`}>
                {results.success && results.events_created > 0 ? (
                  <CheckCircle size={20} className="text-green-600" />
                ) : (
                  <AlertCircle size={20} className={results.success ? 'text-yellow-600' : 'text-red-600'} />
                )}
                <div>
                  <h3 className={`font-medium ${
                    results.success && results.events_created > 0
                      ? 'text-green-800'
                      : results.success
                      ? 'text-yellow-800'
                      : 'text-red-800'
                  }`}>
                    {results.message}
                  </h3>
                  {results.events_created > 0 && (
                    <p className="text-sm text-green-700">
                      {results.events_created} event(s) added to your calendar
                      {results.events_failed > 0 && `, ${results.events_failed} failed`}
                    </p>
                  )}
                </div>
              </div>

              {/* Created Events */}
              {results.created_events.length > 0 && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-3 flex items-center space-x-2">
                    <Calendar size={16} />
                    <span>Successfully Created Events</span>
                  </h4>
                  <div className="space-y-2">
                    {results.created_events.map((event, index) => (
                      <div key={index} className="bg-green-50 border border-green-200 rounded-lg p-3">
                        <h5 className="font-medium text-green-900">{event.title}</h5>
                        <p className="text-sm text-green-700">
                          {formatDateTime(event.start)} - {formatDateTime(event.end)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Failed Events */}
              {results.failed_events.length > 0 && (
                <div>
                  <h4 className="font-medium text-red-900 mb-3">Failed Events</h4>
                  <div className="space-y-2">
                    {results.failed_events.map((failure, index) => (
                      <div key={index} className="bg-red-50 border border-red-200 rounded-lg p-3">
                        <p className="text-sm text-red-800">{failure.error}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex space-x-3 pt-4">
                <button
                  onClick={() => setResults(null)}
                  className="flex-1 bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-lg font-medium transition-colors"
                >
                  Create More Events
                </button>
                <button
                  onClick={handleClose}
                  className="flex-1 bg-gray-500 hover:bg-gray-600 text-white py-2 px-4 rounded-lg font-medium transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};