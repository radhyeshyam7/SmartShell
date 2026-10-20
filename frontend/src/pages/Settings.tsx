import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { AppSettings } from '../types';
import { Key, Shield, Clock, CheckCircle2, AlertTriangle, RefreshCw, Save, Server, HardDrive } from 'lucide-react';

export const Settings: React.FC = () => {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [testResult, setTestResult] = useState<{ success?: boolean; message?: string } | null>(null);
  const [testingKey, setTestingKey] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const data = await api.getSettings();
      setSettings(data);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to load settings' });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!settings) return;

    try {
      setSaving(true);
      setMessage(null);

      const updateData: Partial<AppSettings> = {
        model_name: settings.model_name,
        execution_timeout: settings.execution_timeout,
        auto_approve_low_risk: settings.auto_approve_low_risk,
        allow_all_directories: settings.allow_all_directories,
        ai_provider: settings.ai_provider,
        local_model_url: settings.local_model_url,
      };

      if (apiKeyInput.trim()) {
        updateData.gemini_api_key = apiKeyInput.trim();
      }

      const updated = await api.updateSettings(updateData);
      setSettings(updated);
      setApiKeyInput('');
      setMessage({ type: 'success', text: 'System settings saved successfully!' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to save settings' });
    } finally {
      setSaving(false);
    }
  };

  const handleTestApiKey = async () => {
    if (!apiKeyInput.trim() && !settings?.gemini_api_key_configured) {
      setTestResult({ success: false, message: 'Please enter an API key to test.' });
      return;
    }

    try {
      setTestingKey(true);
      setTestResult(null);
      const result = await api.testApiKey(apiKeyInput.trim() || undefined);
      setTestResult({
        success: result.valid,
        message: result.valid ? 'Gemini API key verified successfully!' : (result.error || 'Invalid API key'),
      });
    } catch (err: any) {
      setTestResult({
        success: false,
        message: err.response?.data?.detail || 'API key verification failed',
      });
    } finally {
      setTestingKey(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <RefreshCw className="animate-spin text-cyan-400" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <Server className="text-cyan-400" size={28} />
          System & Safety Settings
        </h1>
        <p className="text-slate-400 text-sm">
          Configure Gemini AI integration, multi-drive filesystem boundaries, and safety controls.
        </p>
      </div>

      {message && (
        <div
          className={`p-4 rounded-lg flex items-center gap-3 border ${
            message.type === 'success'
              ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-300'
              : 'bg-rose-950/40 border-rose-500/50 text-rose-300'
          }`}
        >
          {message.type === 'success' ? <CheckCircle2 size={20} /> : <AlertTriangle size={20} />}
          <span>{message.text}</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Multi-Drive Access Boundaries */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center gap-2 text-slate-200 font-semibold border-b border-slate-800 pb-3">
            <HardDrive className="text-cyan-400" size={20} />
            <h2>Filesystem Boundary & Drive Permissions</h2>
          </div>

          <div className="flex items-center justify-between pt-2">
            <div>
              <span className="text-sm font-medium text-slate-300 block">
                Full-Drive Access Mode (C:\, D:\, E:\, etc.)
              </span>
              <span className="text-xs text-slate-500">
                Allow SmartShell to browse and operate on all mounted Windows drives accessible to current user permissions.
              </span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings?.allow_all_directories ?? true}
                onChange={(e) =>
                  setSettings(
                    settings ? { ...settings, allow_all_directories: e.target.checked } : null
                  )
                }
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-600"></div>
            </label>
          </div>
        </div>

        {/* Gemini AI Configuration */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center gap-2 text-slate-200 font-semibold border-b border-slate-800 pb-3">
            <Key className="text-cyan-400" size={20} />
            <h2>Gemini AI & Model Settings</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Gemini API Key
              </label>
              <div className="flex gap-2">
                <input
                  type="password"
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  placeholder={
                    settings?.gemini_api_key_configured
                      ? '•••••••••••••••••••••••••••••••• (Configured)'
                      : 'Enter Google Gemini API Key'
                  }
                  className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-cyan-500"
                />
                <button
                  type="button"
                  onClick={handleTestApiKey}
                  disabled={testingKey}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 rounded-lg text-sm font-medium flex items-center gap-2 transition disabled:opacity-50"
                >
                  {testingKey ? <RefreshCw className="animate-spin" size={16} /> : 'Test Key'}
                </button>
              </div>
              {testResult && (
                <p
                  className={`mt-2 text-xs flex items-center gap-1 ${
                    testResult.success ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {testResult.success ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
                  {testResult.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Active Gemini Model
              </label>
              <select
                value={settings?.model_name || 'gemini-3.5-flash-lite'}
                onChange={(e) =>
                  setSettings(settings ? { ...settings, model_name: e.target.value } : null)
                }
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-cyan-500"
              >
                <option value="gemini-3.5-flash-lite">Gemini 3.5 Flash-Lite (Recommended - Ultra Fast)</option>
                <option value="gemini-3.5-flash">Gemini 3.5 Flash (Standard)</option>
                <option value="gemini-3.8-flash">Gemini 3.8 Flash (High Context)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Execution Safety Controls */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center gap-2 text-slate-200 font-semibold border-b border-slate-800 pb-3">
            <Shield className="text-cyan-400" size={20} />
            <h2>Execution Safety Controls</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1 flex items-center gap-2">
                <Clock size={16} className="text-slate-400" />
                Default Subprocess Timeout (seconds)
              </label>
              <input
                type="number"
                min="5"
                max="300"
                value={settings?.execution_timeout || 60}
                onChange={(e) =>
                  setSettings(
                    settings
                      ? { ...settings, execution_timeout: parseInt(e.target.value) || 60 }
                      : null
                  )
                }
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg font-medium flex items-center gap-2 shadow-lg transition disabled:opacity-50"
          >
            {saving ? <RefreshCw className="animate-spin" size={18} /> : <Save size={18} />}
            Save Configuration
          </button>
        </div>
      </form>
    </div>
  );
};
