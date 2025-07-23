import React from 'react';
import { CalendarEvent } from '../types/calendar';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isSameDay, isToday } from 'date-fns';

interface CalendarGridProps {
  currentDate: Date;
  events: CalendarEvent[];
  onDateSelect: (date: Date) => void;
  selectedDate: Date | null;
}

export const CalendarGrid: React.FC<CalendarGridProps> = ({
  currentDate,
  events,
  onDateSelect,
  selectedDate,
}) => {
  const monthStart = startOfMonth(currentDate);
  const monthEnd = endOfMonth(currentDate);
  
  // Get all days including padding for calendar grid
  const startDate = new Date(monthStart);
  startDate.setDate(startDate.getDate() - monthStart.getDay());
  
  const endDate = new Date(monthEnd);
  endDate.setDate(endDate.getDate() + (6 - monthEnd.getDay()));
  
  const days = eachDayOfInterval({ start: startDate, end: endDate });

  const getEventsForDay = (date: Date) => {
    return events.filter(event => {
      const eventDate = event.start.dateTime 
        ? new Date(event.start.dateTime)
        : new Date(event.start.date + 'T00:00:00');
      return isSameDay(eventDate, date);
    });
  };

  // Find the busiest day (most events in the month)
  const eventCounts: Record<string, number> = {};
  events.forEach(event => {
    const eventDate = event.start.dateTime
      ? new Date(event.start.dateTime)
      : new Date(event.start.date + 'T00:00:00');
    const key = eventDate.toDateString();
    eventCounts[key] = (eventCounts[key] || 0) + 1;
  });
  let busiestDay: Date | null = null;
  let maxEvents = 0;
  Object.entries(eventCounts).forEach(([dateStr, count]) => {
    if (count > maxEvents) {
      maxEvents = count;
      busiestDay = new Date(dateStr);
    }
  });

  const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Week day headers */}
      <div className="grid grid-cols-7 bg-gray-50 border-b border-gray-200">
        {weekDays.map(day => (
          <div key={day} className="p-4 text-center font-semibold text-gray-600 text-sm">
            {day}
          </div>
        ))}
      </div>
      
      {/* Calendar grid */}
      <div className="grid grid-cols-7">
        {days.map((day, index) => {
          const dayEvents = getEventsForDay(day);
          const isCurrentMonth = isSameMonth(day, currentDate);
          const isSelected = selectedDate && isSameDay(day, selectedDate);
          const isTodayDate = isToday(day);
          const isWeekend = day.getDay() === 0 || day.getDay() === 6;
          const isBusiest = busiestDay && isSameDay(day, busiestDay);
          // Compose background class: busiest day always takes precedence
          let bgClass = '';
          if (isBusiest) {
            bgClass = 'bg-red-100';
          } else if (isWeekend) {
            bgClass = 'bg-green-50';
          } else if (isCurrentMonth) {
            bgClass = 'bg-white hover:bg-gray-50';
          } else {
            bgClass = 'bg-gray-50 text-gray-400 hover:bg-gray-100';
          }
          return (
            <div
              key={index}
              onClick={() => onDateSelect(day)}
              className={`
                min-h-[120px] p-2 border-r border-b border-gray-100 cursor-pointer transition-colors duration-150
                ${bgClass}
                ${isSelected ? 'bg-blue-50 border-blue-200' : ''}
                ${isTodayDate ? 'ring-2 ring-blue-500 ring-inset' : ''}
              `}
            >
              <div className={`
                text-sm font-medium mb-1 
                ${isBusiest ? 'text-red-600' : isTodayDate ? 'text-blue-600' : isCurrentMonth ? 'text-gray-900' : 'text-gray-400'}
              `}>
                {format(day, 'd')}
              </div>
              
              {/* Event indicators */}
              <div className="space-y-1">
                {dayEvents.slice(0, 3).map((event, eventIndex) => (
                  <div
                    key={event.id}
                    className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full truncate max-w-full mb-1"
                    style={{lineHeight: '1.2'}}
                    title={event.summary}
                  >
                    {event.summary}
                  </div>
                ))}
                {dayEvents.length > 3 && (
                  <div className={`text-xs font-medium ${isBusiest ? 'text-white' : 'text-gray-500'}`}>
                    +{dayEvents.length - 3} more
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};