import React, { useState } from 'react';
import { CalendarEvent } from '../types/calendar';
import { format } from 'date-fns';
import { Clock, FileText, X } from 'lucide-react';

interface EventDetailsProps {
  events: CalendarEvent[];
  selectedDate: Date;
  onClose: () => void;
}

export const EventDetails: React.FC<EventDetailsProps> = ({
  events,
  selectedDate,
  onClose,
}) => {
  // Track expanded state for each event by id
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const toggleExpand = (id: string) => {
    setExpanded(prev => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="bg-white rounded-xl shadow border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          {format(selectedDate, 'EEEE, MMMM d, yyyy')}
        </h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Close"
        >
          <X size={20} />
        </button>
      </div>
      {events.length === 0 ? (
        <p className="text-gray-500 text-center">No events scheduled for this day.</p>
      ) : (
        <div className="space-y-4">
          {events.map((event) => {
            const startTime = event.start.dateTime
              ? format(new Date(event.start.dateTime), 'h:mm a')
              : 'All day';
            const endTime = event.end.dateTime
              ? format(new Date(event.end.dateTime), 'h:mm a')
              : '';
            const desc = event.description || '';
            const isLong = desc.length > 100;
            const isExpanded = expanded[event.id];
            return (
              <div key={event.id} className="border border-gray-100 rounded-lg p-4 mb-2">
                <h4 className="font-semibold text-gray-900 mb-2 text-base">
                  {event.summary}
                </h4>
                <div className="flex items-center space-x-2 text-sm text-gray-700 mb-1">
                  <Clock size={16} className="text-blue-500" />
                  <span>{startTime}{endTime && ` - ${endTime}`}</span>
                </div>
                {desc && (
                  <div className="flex items-start space-x-2 text-sm text-gray-600 mt-1">
                    <FileText size={16} className="text-blue-400 mt-0.5" />
                    <div>
                      <p className="whitespace-pre-line inline">
                        {isLong && !isExpanded ? desc.slice(0, 100) + '...' : desc}
                      </p>
                      {isLong && (
                        <button
                          onClick={() => toggleExpand(event.id)}
                          className="ml-2 text-blue-600 hover:underline text-xs font-medium"
                        >
                          {isExpanded ? 'View less' : 'View more'}
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};