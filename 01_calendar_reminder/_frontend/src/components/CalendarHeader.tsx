import React from 'react';
import { ChevronLeft, ChevronRight, Calendar, RefreshCw, Settings, LogOut, Sparkles } from 'lucide-react';
import { format, addMonths, subMonths } from 'date-fns';

interface CalendarHeaderProps {
  currentDate: Date;
  onPrevMonth: () => void;
  onNextMonth: () => void;
  onToday: () => void;
  onRefresh: () => void;
  onSettings: () => void;
  onSignOut: () => void;
  onQuickEvent: () => void;
  refreshing?: boolean;
}

export const CalendarHeader: React.FC<CalendarHeaderProps> = ({
  currentDate,
  onPrevMonth,
  onNextMonth,
  onToday,
  onRefresh,
  onSettings,
  onSignOut,
  onQuickEvent,
  refreshing = false,
}) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-4 mb-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-3xl font-bold text-gray-900">
            {format(currentDate, 'MMMM yyyy')}
          </h1>
          <button
            onClick={onToday}
            className="flex items-center space-x-2 bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded-lg transition-colors duration-200 text-sm"
          >
            <Calendar size={16} />
            <span>Today</span>
          </button>
          <button
            onClick={onQuickEvent}
            className="flex items-center space-x-2 bg-purple-500 hover:bg-purple-600 text-white px-3 py-2 rounded-lg transition-colors duration-200 text-sm"
          >
            <Sparkles size={16} />
            <span>Quick Add</span>
          </button>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={onRefresh}
            disabled={refreshing}
            className="flex items-center space-x-2 bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-white px-3 py-2 rounded-lg transition-colors duration-200 text-sm"
            title="Refresh calendar events"
          >
            <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
          
          <div className="h-6 w-px bg-gray-300 mx-2"></div>
          
          <button
            onClick={onPrevMonth}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors duration-200"
            title="Previous month"
          >
            <ChevronLeft size={20} className="text-gray-600" />
          </button>
          <button
            onClick={onNextMonth}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors duration-200"
            title="Next month"
          >
            <ChevronRight size={20} className="text-gray-600" />
          </button>
          
          <div className="h-6 w-px bg-gray-300 mx-2"></div>
          
          <button
            onClick={onSettings}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors duration-200"
            title="Settings"
          >
            <Settings size={20} className="text-gray-600" />
          </button>
          <button
            onClick={onSignOut}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors duration-200"
            title="Sign out"
          >
            <LogOut size={20} className="text-gray-600" />
          </button>
        </div>
      </div>
    </div>
  );
};