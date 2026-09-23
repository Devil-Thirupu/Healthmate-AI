import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import {
  Bell,
  CheckCheck,
  CheckCircle2,
  Clock,
  Pill,
  FileText,
  CalendarCheck,
  AlertCircle,
  ExternalLink,
  X
} from 'lucide-react';

const NotificationCenter = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('reminders'); // 'reminders' | 'all'
  const [notificationData, setNotificationData] = useState({
    unread_count: 0,
    notifications: [],
    today_reminders_count: 0,
    upcoming_reminders_count: 0
  });
  const [todayReminders, setTodayReminders] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const dropdownRef = useRef(null);

  const fetchNotifications = async () => {
    try {
      const [notifRes, remRes] = await Promise.allSettled([
        api.get('/notifications'),
        api.get('/reminders/today')
      ]);

      if (notifRes.status === 'fulfilled') {
        setNotificationData(notifRes.value.data);
      }
      if (remRes.status === 'fulfilled') {
        setTodayReminders(remRes.value.data || []);
      }
    } catch (err) {
      console.error('Error fetching notification center data:', err);
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 60000);
    const handleRefresh = () => fetchNotifications();
    window.addEventListener('healthmate_reminder_updated', handleRefresh);
    window.addEventListener('healthmate_doc_uploaded', handleRefresh);

    return () => {
      clearInterval(interval);
      window.removeEventListener('healthmate_reminder_updated', handleRefresh);
      window.removeEventListener('healthmate_doc_uploaded', handleRefresh);
    };
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const handleMarkAllRead = async () => {
    try {
      await api.post('/notifications/read-all');
      fetchNotifications();
    } catch (err) {
      console.error('Error marking all as read:', err);
    }
  };

  const handleMarkSingleRead = async (id) => {
    try {
      await api.post(`/notifications/${id}/read`);
      fetchNotifications();
    } catch (err) {
      console.error('Error marking notification read:', err);
    }
  };

  const handleCompleteReminder = async (id) => {
    try {
      await api.post(`/reminders/${id}/complete`);
      fetchNotifications();
      window.dispatchEvent(new Event('healthmate_reminder_updated'));
    } catch (err) {
      console.error('Error completing reminder:', err);
    }
  };

  const handleSnoozeReminder = async (id) => {
    try {
      await api.post(`/reminders/${id}/snooze`, { snooze_minutes: 30 });
      fetchNotifications();
      window.dispatchEvent(new Event('healthmate_reminder_updated'));
    } catch (err) {
      console.error('Error snoozing reminder:', err);
    }
  };

  const totalBadgeCount = (notificationData.unread_count || 0) + 
    (todayReminders.filter(r => r.status !== 'COMPLETED').length || 0);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-300 dark:hover:text-white dark:hover:bg-slate-800 transition-colors focus:outline-none"
        title="Notifications & Medication Reminders"
        aria-label="Notifications"
      >
        <Bell className="w-4 h-4" />
        {totalBadgeCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center bg-rose-500 text-white text-[10px] font-bold rounded-full px-1 shadow-xs ring-2 ring-white dark:ring-slate-900 animate-pulse">
            {totalBadgeCount > 99 ? '99+' : totalBadgeCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200/90 dark:border-slate-800 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
          <div className="px-4 py-3 bg-slate-50/80 dark:bg-slate-800/80 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Bell className="w-4 h-4 text-teal-600" />
              <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-heading">
                Clinical Notification Hub
              </h3>
            </div>
            {notificationData.unread_count > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-[11px] font-bold text-teal-600 hover:text-teal-700 hover:underline flex items-center space-x-1"
              >
                <CheckCheck className="w-3.5 h-3.5" />
                <span>Mark all read</span>
              </button>
            )}
          </div>

          <div className="flex border-b border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs">
            <button
              onClick={() => setActiveTab('reminders')}
              className={`flex-1 py-2 text-center font-bold transition-colors flex items-center justify-center space-x-1.5 ${
                activeTab === 'reminders'
                  ? 'text-teal-700 border-b-2 border-teal-600 bg-teal-50/40'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Pill className="w-3.5 h-3.5" />
              <span>Today's Doses ({todayReminders.filter(r => r.status !== 'COMPLETED').length})</span>
            </button>
            <button
              onClick={() => setActiveTab('all')}
              className={`flex-1 py-2 text-center font-bold transition-colors flex items-center justify-center space-x-1.5 ${
                activeTab === 'all'
                  ? 'text-teal-700 border-b-2 border-teal-600 bg-teal-50/40'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Bell className="w-3.5 h-3.5" />
              <span>Alerts ({notificationData.unread_count})</span>
            </button>
          </div>

          <div className="max-h-80 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800/60 p-2 space-y-1">
            {activeTab === 'reminders' && (
              todayReminders.length === 0 ? (
                <div className="p-6 text-center text-slate-400">
                  <Pill className="w-8 h-8 mx-auto mb-2 opacity-40 text-teal-600" />
                  <p className="text-xs font-semibold">No medication reminders for today.</p>
                </div>
              ) : (
                todayReminders.map((rem) => (
                  <div
                    key={rem.id}
                    className={`p-3 rounded-xl transition-all ${
                      rem.status === 'COMPLETED'
                        ? 'bg-slate-50 dark:bg-slate-800/40 opacity-60'
                        : 'bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 shadow-2xs'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-2">
                        <div className="w-7 h-7 rounded-lg bg-teal-50 dark:bg-teal-950 text-teal-600 flex items-center justify-center shrink-0 mt-0.5">
                          <Pill className="w-3.5 h-3.5" />
                        </div>
                        <div>
                          <p className="text-xs font-bold text-slate-900 dark:text-white">
                            {rem.medicine_name} <span className="font-normal text-slate-500 text-[11px]">— {rem.dosage || 'Prescribed'}</span>
                          </p>
                          <div className="flex items-center space-x-2 mt-1 text-[11px] text-slate-500">
                            <span className="inline-flex items-center space-x-1 font-bold text-teal-700">
                              <Clock className="w-3 h-3" />
                              <span>{rem.scheduled_time || rem.timing || 'As Prescribed'}</span>
                            </span>
                            <span>•</span>
                            <span className="truncate max-w-[120px]">{rem.frequency || 'Daily'}</span>
                          </div>
                        </div>
                      </div>

                      {rem.status === 'COMPLETED' ? (
                        <span className="inline-flex items-center space-x-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          <span>Done</span>
                        </span>
                      ) : (
                        <div className="flex items-center space-x-1">
                          <button
                            onClick={() => handleSnoozeReminder(rem.id)}
                            className="text-[10px] px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg transition-colors"
                          >
                            Snooze
                          </button>
                          <button
                            onClick={() => handleCompleteReminder(rem.id)}
                            className="text-[10px] px-2.5 py-1 bg-teal-600 hover:bg-teal-700 text-white font-bold rounded-lg shadow-2xs transition-colors"
                          >
                            Done
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )
            )}

            {activeTab === 'all' && (
              notificationData.notifications.length === 0 ? (
                <div className="p-6 text-center text-slate-400">
                  <Bell className="w-8 h-8 mx-auto mb-2 opacity-40 text-teal-600" />
                  <p className="text-xs font-semibold">No alerts right now.</p>
                </div>
              ) : (
                notificationData.notifications.map((notif) => (
                  <div
                    key={notif.id}
                    onClick={() => !notif.is_read && handleMarkSingleRead(notif.id)}
                    className={`p-3 rounded-xl transition-all cursor-pointer ${
                      notif.is_read
                        ? 'bg-transparent text-slate-600'
                        : 'bg-teal-50/50 dark:bg-teal-950/40 border border-teal-100 font-medium'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-2">
                        <div className="w-7 h-7 rounded-lg bg-teal-100 dark:bg-teal-900 text-teal-700 flex items-center justify-center shrink-0 mt-0.5">
                          {notif.type === 'MEDICATION_REMINDER' ? (
                            <Pill className="w-3.5 h-3.5" />
                          ) : notif.type === 'REPORT_INSIGHT' ? (
                            <FileText className="w-3.5 h-3.5" />
                          ) : (
                            <Bell className="w-3.5 h-3.5" />
                          )}
                        </div>
                        <div>
                          <p className="text-xs font-bold text-slate-900 dark:text-white">{notif.title}</p>
                          <p className="text-[11px] text-slate-600 dark:text-slate-300 mt-0.5 leading-relaxed">{notif.message}</p>
                          <p className="text-[9px] text-slate-400 mt-1">
                            {new Date(notif.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                      </div>
                      {!notif.is_read && (
                        <span className="w-2 h-2 rounded-full bg-teal-600 shrink-0 mt-1.5"></span>
                      )}
                    </div>
                  </div>
                ))
              )
            )}
          </div>

          <div className="px-4 py-2.5 bg-slate-50 dark:bg-slate-800/80 border-t border-slate-100 dark:border-slate-800 text-center">
            <Link
              to="/prescriptions"
              onClick={() => setIsOpen(false)}
              className="text-xs font-bold text-teal-600 hover:text-teal-700 hover:underline inline-flex items-center space-x-1"
            >
              <span>Manage Medication Schedule</span>
              <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationCenter;
