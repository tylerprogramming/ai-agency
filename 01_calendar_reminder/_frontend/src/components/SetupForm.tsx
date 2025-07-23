import React, { useState } from 'react';
import { Key, ExternalLink, CheckCircle } from 'lucide-react';

interface SetupFormProps {
  onClientIdSave: (clientId: string) => void;
}

export const SetupForm: React.FC<SetupFormProps> = ({ onClientIdSave }) => {
  const [clientId, setClientId] = useState('');
  const [isValid, setIsValid] = useState(false);

  const handleClientIdChange = (value: string) => {
    setClientId(value);
    // Basic validation for Google Client ID format
    const isValidFormat = value.includes('.apps.googleusercontent.com') && value.length > 50;
    setIsValid(isValidFormat);
  };

  const handleSave = () => {
    if (isValid) {
      localStorage.setItem('google_client_id', clientId);
      onClientIdSave(clientId);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-2xl w-full">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="text-center mb-8">
            <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
              <Key size={32} className="text-blue-600" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Setup Google Calendar</h1>
            <p className="text-gray-600">
              Enter your Google OAuth Client ID to get started with your calendar
            </p>
          </div>

          <div className="space-y-6">
            <div>
              <label htmlFor="clientId" className="block text-sm font-medium text-gray-700 mb-2">
                Google OAuth Client ID
              </label>
              <input
                id="clientId"
                type="text"
                value={clientId}
                onChange={(e) => handleClientIdChange(e.target.value)}
                placeholder="123456789-abcdefghijklmnop.apps.googleusercontent.com"
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                  clientId && !isValid ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {clientId && !isValid && (
                <p className="mt-2 text-sm text-red-600">
                  Please enter a valid Google Client ID (should end with .apps.googleusercontent.com)
                </p>
              )}
              {isValid && (
                <div className="mt-2 flex items-center text-sm text-green-600">
                  <CheckCircle size={16} className="mr-1" />
                  Valid Client ID format
                </div>
              )}
            </div>

            <button
              onClick={handleSave}
              disabled={!isValid}
              className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
                isValid
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              Save and Continue
            </button>
          </div>

          <div className="mt-8 p-6 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
              <ExternalLink size={18} className="mr-2" />
              How to get your Client ID:
            </h3>
            <ol className="list-decimal list-inside text-sm text-gray-700 space-y-2">
              <li>
                Go to{' '}
                <a
                  href="https://console.cloud.google.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 underline"
                >
                  Google Cloud Console
                </a>
              </li>
              <li>Create a new project or select an existing one</li>
              <li>
                Enable the{' '}
                <a
                  href="https://console.cloud.google.com/apis/library/calendar-json.googleapis.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 underline"
                >
                  Google Calendar API
                </a>
              </li>
              <li>Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"</li>
              <li>Choose "Web application" as the application type</li>
              <li>
                Add <code className="bg-gray-200 px-1 rounded">{window.location.origin}</code> to "Authorized JavaScript origins"
              </li>
              <li>Copy the generated Client ID and paste it above</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
};