import { useState } from 'react';
import { User, Shield, Bell } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { clsx } from 'clsx';

type SettingsTab = 'profile' | 'account' | 'security';

const tabs: { id: SettingsTab; label: string; icon: React.ElementType }[] = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'account', label: 'Account', icon: Bell },
  { id: 'security', label: 'Security', icon: Shield },
];

export function SettingsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');

  return (
    <div className="p-6 max-w-3xl mx-auto animate-fade-in">
      <h1 className="text-xl font-semibold mb-6">Settings</h1>

      <div className="flex gap-6">
        {/* Sidebar tabs */}
        <nav className="w-44 flex-shrink-0">
          <p className="section-header mb-2">Configuration</p>
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={clsx(
                  'sidebar-item w-full',
                  activeTab === tab.id && 'sidebar-item-active'
                )}
              >
                <Icon size={14} />
                {tab.label}
              </button>
            );
          })}
        </nav>

        {/* Panel */}
        <div className="flex-1 min-w-0">
          {activeTab === 'profile' && (
            <div className="card p-5 animate-fade-in">
              <h2 className="text-sm font-semibold mb-4">Profile</h2>
              <div className="flex items-center gap-4 mb-5 pb-5 border-b border-surface-border">
                <div className="w-12 h-12 rounded-full bg-brand/20 border border-brand/30 flex items-center justify-center">
                  <span className="text-lg font-bold text-brand-light">
                    {user?.name?.charAt(0).toUpperCase() ?? 'U'}
                  </span>
                </div>
                <div>
                  <p className="text-sm font-medium">{user?.name}</p>
                  <p className="text-xs text-text-muted">{user?.email}</p>
                </div>
              </div>
              <div className="space-y-4">
                <Input
                  id="settings-name"
                  label="Full Name"
                  defaultValue={user?.name}
                  placeholder="Your full name"
                />
                <Input
                  id="settings-email"
                  label="Email"
                  type="email"
                  defaultValue={user?.email}
                  placeholder="your@email.com"
                  hint="Email changes are not yet implemented."
                />
                <div className="flex justify-end pt-2">
                  <Button variant="secondary" disabled className="text-sm">
                    Save Changes
                    <span className="ml-2 text-[10px] text-text-muted">Coming Soon</span>
                  </Button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'account' && (
            <div className="card p-5 animate-fade-in">
              <h2 className="text-sm font-semibold mb-4">Account</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between py-3 border-b border-surface-border">
                  <div>
                    <p className="text-sm font-medium">Notification Preferences</p>
                    <p className="text-xs text-text-muted">Email and in-app notification settings</p>
                  </div>
                  <span className="text-[11px] text-text-muted bg-surface-border rounded px-2 py-1">
                    Coming Soon
                  </span>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-surface-border">
                  <div>
                    <p className="text-sm font-medium">API Keys</p>
                    <p className="text-xs text-text-muted">Manage programmatic access tokens</p>
                  </div>
                  <span className="text-[11px] text-text-muted bg-surface-border rounded px-2 py-1">
                    Coming Soon
                  </span>
                </div>
                <div className="flex items-center justify-between py-3">
                  <div>
                    <p className="text-sm font-medium text-accent-red">Delete Account</p>
                    <p className="text-xs text-text-muted">Permanently delete your account and all data</p>
                  </div>
                  <Button variant="danger" disabled className="text-xs">
                    Delete Account
                  </Button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="card p-5 animate-fade-in">
              <h2 className="text-sm font-semibold mb-4">Security</h2>
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium mb-3">Change Password</h3>
                  <div className="space-y-3">
                    <Input
                      id="settings-current-password"
                      label="Current Password"
                      type="password"
                      placeholder="••••••••"
                      hint="Password changes are not yet implemented."
                    />
                    <Input
                      id="settings-new-password"
                      label="New Password"
                      type="password"
                      placeholder="Min. 8 characters"
                    />
                    <Input
                      id="settings-confirm-password"
                      label="Confirm New Password"
                      type="password"
                      placeholder="Repeat new password"
                    />
                    <div className="flex justify-end pt-1">
                      <Button variant="secondary" disabled className="text-sm">
                        Update Password
                        <span className="ml-2 text-[10px] text-text-muted">Coming Soon</span>
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="border-t border-surface-border pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">Two-Factor Authentication</p>
                      <p className="text-xs text-text-muted">Add an extra layer of security</p>
                    </div>
                    <span className="text-[11px] text-text-muted bg-surface-border rounded px-2 py-1">
                      Coming Soon
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
