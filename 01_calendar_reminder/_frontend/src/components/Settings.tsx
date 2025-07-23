import React, { useState } from 'react';
import { Settings as SettingsIcon, Copy, Check, X, Save, Eye, EyeOff, Send, TestTube } from 'lucide-react';

interface SettingsProps {
  currentClientId: string | null;
  onClientIdUpdate: (clientId: string) => void;
  onClose: () => void;
}

export const Settings: React.FC<SettingsProps> = ({
  currentClientId,
  onClientIdUpdate,
  onClose,
}) => {
  const [clientId, setClientId] = useState(currentClientId || '');
  const [isEditing, setIsEditing] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isValid, setIsValid] = useState(true);

  // Telegram ID state
  const [telegramId, setTelegramId] = useState(() => localStorage.getItem('telegram_user_id') || '');
  const [isEditingTelegram, setIsEditingTelegram] = useState(!telegramId); // Always editing if empty
  const [telegramDraft, setTelegramDraft] = useState(telegramId);

  // Telegram Bot Token state
  const [telegramToken, setTelegramToken] = useState(() => localStorage.getItem('telegram_bot_token') || '');
  const [isEditingToken, setIsEditingToken] = useState(!telegramToken);
  const [tokenDraft, setTokenDraft] = useState(telegramToken);
  const [showToken, setShowToken] = useState(false);

  // Daily Schedule Time state
  const [scheduleHour, setScheduleHour] = useState(() => parseInt(localStorage.getItem('schedule_hour') || '9'));
  const [scheduleMinute, setScheduleMinute] = useState(() => parseInt(localStorage.getItem('schedule_minute') || '0'));
  const [scheduleEnabled, setScheduleEnabled] = useState(() => localStorage.getItem('schedule_enabled') === 'true');

  // OpenAI API Key state
  const [openaiKey, setOpenaiKey] = useState(() => localStorage.getItem('openai_api_key') || '');
  const [isEditingOpenai, setIsEditingOpenai] = useState(!openaiKey); // Always editing if empty
  const [openaiDraft, setOpenaiDraft] = useState(openaiKey);
  const [showOpenai, setShowOpenai] = useState(false);

  const currentOrigin = window.location.origin;

  const handleClientIdChange = (value: string) => {
    setClientId(value);
    const isValidFormat = value.includes('.apps.googleusercontent.com') && value.length > 50;
    setIsValid(isValidFormat);
  };

  const handleSave = () => {
    if (isValid && clientId !== currentClientId) {
      localStorage.setItem('google_client_id', clientId);
      onClientIdUpdate(clientId);
      setIsEditing(false);
    }
  };

  const handleCopyOrigin = async () => {
    try {
      await navigator.clipboard.writeText(currentOrigin);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const maskClientId = (id: string) => {
    if (id.length < 20) return id;
    return id.substring(0, 12) + '...' + id.substring(id.length - 12);
  };

  const handleTelegramSave = async () => {
    setTelegramId(telegramDraft);
    localStorage.setItem('telegram_user_id', telegramDraft);
    setIsEditingTelegram(false);
    
    // Update scheduled reminder if we have both token and chat ID
    if (telegramToken && telegramDraft) {
      await updateScheduledReminder();
    }
  };

  const handleTelegramCancel = () => {
    setTelegramDraft(telegramId);
    setIsEditingTelegram(false);
  };

  const handleOpenaiSave = () => {
    setOpenaiKey(openaiDraft);
    localStorage.setItem('openai_api_key', openaiDraft);
    setIsEditingOpenai(false);
  };

  const handleOpenaiCancel = () => {
    setOpenaiDraft(openaiKey);
    setIsEditingOpenai(false);
  };

  const handleTokenSave = async () => {
    setTelegramToken(tokenDraft);
    localStorage.setItem('telegram_bot_token', tokenDraft);
    setIsEditingToken(false);
    
    // Update scheduled reminder if we have both token and chat ID
    if (tokenDraft && telegramId) {
      await updateScheduledReminder();
    }
  };

  const handleTokenCancel = () => {
    setTokenDraft(telegramToken);
    setIsEditingToken(false);
  };

  const handleScheduleChange = async () => {
    localStorage.setItem('schedule_hour', scheduleHour.toString());
    localStorage.setItem('schedule_minute', scheduleMinute.toString());
    localStorage.setItem('schedule_enabled', scheduleEnabled.toString());
    
    // Auto-schedule when settings change and we have all required info
    if (telegramToken && telegramId) {
      await updateScheduledReminder();
    }
  };

  const updateScheduledReminder = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/schedule-daily-reminder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bot_token: telegramToken,
          chat_id: telegramId,
          hour: scheduleHour,
          minute: scheduleMinute,
          enabled: scheduleEnabled,
          user_id: 'default_user'
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Schedule updated:', result);
        setReminderStatus({
          scheduled: result.enabled,
          next_run: result.next_run
        });
      } else {
        console.error('Failed to update schedule');
      }
    } catch (error) {
      console.error('Error updating schedule:', error);
    }
  };

  const [testingTelegram, setTestingTelegram] = useState(false);
  const [sendingDaily, setSendingDaily] = useState(false);
  const [reminderStatus, setReminderStatus] = useState<{scheduled: boolean, next_run?: string} | null>(null);

  const testTelegramConnection = async () => {
    if (!telegramToken || !telegramId) {
      alert('Please set both Telegram Bot Token and User ID first');
      return;
    }

    setTestingTelegram(true);
    try {
      const response = await fetch('http://localhost:8000/api/test-telegram', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bot_token: telegramToken,
          chat_id: telegramId
        })
      });

      if (response.ok) {
        alert('✅ Test message sent successfully! Check your Telegram.');
      } else {
        const error = await response.json();
        alert(`❌ Failed to send test message: ${error.detail}`);
      }
    } catch (error) {
      alert(`❌ Error testing Telegram: ${error}`);
    } finally {
      setTestingTelegram(false);
    }
  };

  const sendDailySchedule = async () => {
    if (!telegramToken || !telegramId) {
      alert('Please set both Telegram Bot Token and User ID first');
      return;
    }

    setSendingDaily(true);
    try {
      const response = await fetch('http://localhost:8000/api/send-daily-telegram', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bot_token: telegramToken,
          chat_id: telegramId
        })
      });

      if (response.ok) {
        const result = await response.json();
        alert(`✅ Daily schedule sent! Found ${result.events_count} events for today.`);
      } else {
        const error = await response.json();
        alert(`❌ Failed to send daily schedule: ${error.detail}`);
      }
    } catch (error) {
      alert(`❌ Error sending daily schedule: ${error}`);
    } finally {
      setSendingDaily(false);
    }
  };

  const [testingSchedule, setTestingSchedule] = useState(false);

  const testScheduler = async () => {
    if (!telegramToken || !telegramId) {
      alert('Please set both Telegram Bot Token and User ID first');
      return;
    }

    setTestingSchedule(true);
    try {
      const response = await fetch('http://localhost:8000/api/test-schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bot_token: telegramToken,
          chat_id: telegramId
        })
      });

      if (response.ok) {
        const result = await response.json();
        alert(`✅ Test reminder scheduled! You should receive a message at ${new Date(result.scheduled_time).toLocaleTimeString()}`);
      } else {
        const error = await response.json();
        alert(`❌ Failed to schedule test: ${error.detail}`);
      }
    } catch (error) {
      alert(`❌ Error testing scheduler: ${error}`);
    } finally {
      setTestingSchedule(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-gray-100 rounded-lg">
                <SettingsIcon size={20} className="text-gray-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900">Settings</h2>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X size={24} />
            </button>
          </div>

          <div className="space-y-6">
            {/* Current Origin */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Current Origin URL
              </label>
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  value={currentOrigin}
                  readOnly
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-700 text-sm"
                />
                <button
                  onClick={handleCopyOrigin}
                  className="flex items-center space-x-1 bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded-lg transition-colors text-sm"
                >
                  {copied ? <Check size={16} /> : <Copy size={16} />}
                  <span>{copied ? 'Copied!' : 'Copy'}</span>
                </button>
              </div>
              <p className="mt-2 text-xs text-gray-500">
                Add this URL to "Authorized JavaScript origins" in your Google Cloud Console
              </p>
            </div>

            {/* Client ID */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Google OAuth Client ID
                </label>
                {!isEditing && currentClientId && (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    Edit
                  </button>
                )}
              </div>
              {isEditing ? (
                <div className="space-y-3">
                  <input
                    type="text"
                    value={clientId}
                    onChange={(e) => handleClientIdChange(e.target.value)}
                    placeholder="123456789-abcdefghijklmnop.apps.googleusercontent.com"
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors text-sm ${
                      clientId && !isValid ? 'border-red-300' : 'border-gray-300'
                    }`}
                  />
                  {clientId && !isValid && (
                    <p className="text-sm text-red-600">
                      Please enter a valid Google Client ID
                    </p>
                  )}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={handleSave}
                      disabled={!isValid || clientId === currentClientId}
                      className={`flex items-center space-x-1 px-3 py-2 rounded-lg text-sm transition-colors ${
                        isValid && clientId !== currentClientId
                          ? 'bg-green-500 hover:bg-green-600 text-white'
                          : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      }`}
                    >
                      <Save size={16} />
                      <span>Save</span>
                    </button>
                    <button
                      onClick={() => {
                        setIsEditing(false);
                        setClientId(currentClientId || '');
                        setIsValid(true);
                      }}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-700 text-sm font-mono">
                  {currentClientId ? maskClientId(currentClientId) : 'Not configured'}
                </div>
              )}
            </div>

            {/* Telegram User ID */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Telegram User ID
                </label>
                {!isEditingTelegram && telegramId && (
                  <button
                    onClick={() => setIsEditingTelegram(true)}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    Edit
                  </button>
                )}
              </div>
              {(isEditingTelegram || !telegramId) ? (
                <div className="space-y-3">
                  <input
                    type="text"
                    value={telegramDraft}
                    onChange={e => setTelegramDraft(e.target.value)}
                    placeholder="Your Telegram User ID"
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors text-sm border-gray-300"
                  />
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={handleTelegramSave}
                      disabled={telegramDraft === telegramId}
                      className={`flex items-center space-x-1 px-3 py-2 rounded-lg text-sm transition-colors ${
                        telegramDraft !== telegramId
                          ? 'bg-green-500 hover:bg-green-600 text-white'
                          : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      }`}
                    >
                      <Save size={16} />
                      <span>Save</span>
                    </button>
                    <button
                      onClick={handleTelegramCancel}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-700 text-sm font-mono">
                  {telegramId || 'Not configured'}
                </div>
              )}
            </div>

            {/* Telegram Bot Token */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Telegram Bot Token
                </label>
                {!isEditingToken && telegramToken && (
                  <button
                    onClick={() => setIsEditingToken(true)}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    Edit
                  </button>
                )}
              </div>
              {(isEditingToken || !telegramToken) ? (
                <div className="space-y-3">
                  <div className="relative">
                    <input
                      type={showToken ? 'text' : 'password'}
                      value={tokenDraft}
                      onChange={e => setTokenDraft(e.target.value)}
                      placeholder="1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ"
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors text-sm border-gray-300 pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowToken(v => !v)}
                      className="absolute right-2 top-2 text-gray-400 hover:text-gray-600"
                      tabIndex={-1}
                    >
                      {showToken ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={handleTokenSave}
                      disabled={tokenDraft === telegramToken}
                      className={`flex items-center space-x-1 px-3 py-2 rounded-lg text-sm transition-colors ${
                        tokenDraft !== telegramToken
                          ? 'bg-green-500 hover:bg-green-600 text-white'
                          : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      }`}
                    >
                      <Save size={16} />
                      <span>Save</span>
                    </button>
                    <button
                      onClick={handleTokenCancel}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-700 text-sm font-mono">
                  {telegramToken ? '••••••••:••••••••••••••••••••••' : 'Not configured'}
                </div>
              )}
              <p className="mt-2 text-xs text-gray-500">
                Get your bot token from @BotFather on Telegram
              </p>
            </div>

            {/* Daily Schedule Settings */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-4">
                Daily Schedule Settings
              </label>
              <div className="space-y-4 bg-gray-50 p-4 rounded-lg border">
                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    id="schedule-enabled"
                    checked={scheduleEnabled}
                    onChange={(e) => {
                      setScheduleEnabled(e.target.checked);
                      handleScheduleChange();
                    }}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="schedule-enabled" className="text-sm font-medium text-gray-700">
                    Enable daily calendar reminder
                  </label>
                </div>
                
                {scheduleEnabled && (
                  <div className="flex items-center space-x-4">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Hour (24h format)</label>
                      <select
                        value={scheduleHour}
                        onChange={(e) => {
                          setScheduleHour(parseInt(e.target.value));
                          handleScheduleChange();
                        }}
                        className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                      >
                        {Array.from({ length: 24 }, (_, i) => (
                          <option key={i} value={i}>
                            {i.toString().padStart(2, '0')}:00
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Minutes</label>
                      <select
                        value={scheduleMinute}
                        onChange={(e) => {
                          setScheduleMinute(parseInt(e.target.value));
                          handleScheduleChange();
                        }}
                        className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                      >
                        {[0, 15, 30, 45].map(minute => (
                          <option key={minute} value={minute}>
                            :{minute.toString().padStart(2, '0')}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}
                
                <div className="space-y-2">
                  <p className="text-xs text-gray-500">
                    {scheduleEnabled 
                      ? `Daily reminder will be sent at ${scheduleHour.toString().padStart(2, '0')}:${scheduleMinute.toString().padStart(2, '0')} Eastern Time`
                      : 'Daily reminders are disabled'
                    }
                  </p>
                  
                  {reminderStatus && reminderStatus.scheduled && (
                    <div className="flex items-center space-x-2 text-xs">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      <span className="text-green-700 font-medium">
                        Scheduled! Next reminder: {new Date(reminderStatus.next_run || '').toLocaleString()}
                      </span>
                    </div>
                  )}
                  
                  {scheduleEnabled && telegramToken && telegramId && !reminderStatus?.scheduled && (
                    <div className="flex items-center space-x-2 text-xs">
                      <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                      <span className="text-yellow-700">Setting up reminder...</span>
                    </div>
                  )}
                </div>
                
                {/* Test Buttons */}
                {telegramToken && telegramId && (
                  <div className="flex space-x-3 pt-2 border-t border-gray-200">
                    <button
                      onClick={testTelegramConnection}
                      disabled={testingTelegram}
                      className="flex items-center space-x-2 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300 text-white px-3 py-2 rounded-lg transition-colors text-sm"
                    >
                      <TestTube size={16} className={testingTelegram ? 'animate-pulse' : ''} />
                      <span>{testingTelegram ? 'Testing...' : 'Test Connection'}</span>
                    </button>
                    <button
                      onClick={sendDailySchedule}
                      disabled={sendingDaily}
                      className="flex items-center space-x-2 bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-white px-3 py-2 rounded-lg transition-colors text-sm"
                    >
                      <Send size={16} className={sendingDaily ? 'animate-pulse' : ''} />
                      <span>{sendingDaily ? 'Sending...' : 'Send Today\'s Schedule'}</span>
                    </button>
                    <button
                      onClick={testScheduler}
                      disabled={testingSchedule}
                      className="flex items-center space-x-2 bg-purple-500 hover:bg-purple-600 disabled:bg-purple-300 text-white px-3 py-2 rounded-lg transition-colors text-sm"
                    >
                      <TestTube size={16} className={testingSchedule ? 'animate-pulse' : ''} />
                      <span>{testingSchedule ? 'Scheduling...' : 'Test in 1 min'}</span>
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* OpenAI API Key */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  OpenAI API Key
                </label>
                {!isEditingOpenai && openaiKey && (
                  <button
                    onClick={() => setIsEditingOpenai(true)}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    Edit
                  </button>
                )}
              </div>
              {(isEditingOpenai || !openaiKey) ? (
                <div className="space-y-3">
                  <div className="relative">
                    <input
                      type={showOpenai ? 'text' : 'password'}
                      value={openaiDraft}
                      onChange={e => setOpenaiDraft(e.target.value)}
                      placeholder="sk-..."
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors text-sm border-gray-300 pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowOpenai(v => !v)}
                      className="absolute right-2 top-2 text-gray-400 hover:text-gray-600"
                      tabIndex={-1}
                    >
                      {showOpenai ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={handleOpenaiSave}
                      disabled={openaiDraft === openaiKey}
                      className={`flex items-center space-x-1 px-3 py-2 rounded-lg text-sm transition-colors ${
                        openaiDraft !== openaiKey
                          ? 'bg-green-500 hover:bg-green-600 text-white'
                          : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      }`}
                    >
                      <Save size={16} />
                      <span>Save</span>
                    </button>
                    <button
                      onClick={handleOpenaiCancel}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-700 text-sm font-mono flex items-center">
                  <span className="flex-1">{openaiKey ? '••••••••' : 'Not configured'}</span>
                  <button
                    onClick={() => setIsEditingOpenai(true)}
                    className="ml-2 text-blue-600 hover:text-blue-800 text-xs font-medium"
                  >
                    Edit
                  </button>
                </div>
              )}
            </div>

            {/* Instructions */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-medium text-blue-900 mb-2">Setup Instructions:</h3>
              <ol className="list-decimal list-inside text-sm text-blue-800 space-y-1">
                <li>Copy the origin URL above</li>
                <li>Go to Google Cloud Console → APIs & Services → Credentials</li>
                <li>Select your OAuth 2.0 Client ID</li>
                <li>Add the copied URL to "Authorized JavaScript origins"</li>
                <li>Save the changes in Google Cloud Console</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};