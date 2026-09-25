'use client';

import { useState, useEffect, useRef } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useCommandPalette } from '../hooks/useCommandPalette';
import { useTheme } from '../hooks/useTheme';
import { useReducedMotion } from '../hooks/useReducedMotion';

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  badge?: string;
  children?: NavItem[];
}

const navSections: { title: string; items: NavItem[] }[] = [
  {
    title: 'CORE',
    items: [
      { label: 'Dashboard', path: '/admin', icon: <DashboardIcon /> },
      { label: 'Leads', path: '/admin/leads', icon: <LeadsIcon /> },
      { label: 'Integrations', path: '/admin/integrations', icon: <IntegrationsIcon /> },
      { label: 'Accounts', path: '/admin/accounts', icon: <AccountsIcon /> },
    ],
  },
  {
    title: 'AI & MESSAGING',
    items: [
      { label: 'AI Control', path: '/admin/ai-control', icon: <AIControlIcon /> },
      { label: 'Message Engine', path: '/admin/message-engine', icon: <MessageEngineIcon /> },
      { label: 'Voice Agent', path: '/admin/voice-agent', icon: <VoiceAgentIcon /> },
    ],
  },
  {
    title: 'CAMPAIGNS & JOBS',
    items: [
      { label: 'Campaigns', path: '/admin/campaigns', icon: <CampaignsIcon /> },
      { label: 'Jobs', path: '/admin/jobs', icon: <JobsIcon /> },
      { label: 'Logs', path: '/admin/logs', icon: <LogsIcon /> },
    ],
  },
  {
    title: 'SYSTEM',
    items: [
      { label: 'Payments', path: '/admin/payments', icon: <PaymentsIcon /> },
      { label: 'Settings', path: '/admin/settings', icon: <SettingsIcon /> },
    ],
  },
];

function SidebarItem({ item, isCollapsed, isOpen, onToggle, depth = 0 }: { 
  item: NavItem; 
  isCollapsed: boolean; 
  isOpen: boolean; 
  onToggle: () => void; 
  depth?: number;
}) {
  const location = useLocation();
  const isActive = location.pathname === item.path || (item.children && location.pathname.startsWith(item.path));
  const hasChildren = item.children && item.children.length > 0;
  const reducedMotion = useReducedMotion();

  if (isCollapsed && depth === 0 && hasChildren) {
    return (
      <NavLink
        to={item.path}
        className={`sidebar-item ${isActive ? 'active' : ''}`}
        title={item.label}
        aria-label={item.label}
        style={{ paddingLeft: 16 + depth * 12 }}
      >
        <span className="sidebar-icon">{item.icon}</span>
        {item.badge && <span className="sidebar-badge">{item.badge}</span>}
        <AnimatePresence mode="popLayout">
          {isOpen && <ChevronDownIcon className="sidebar-chevron" />}
        </AnimatePresence>
      </NavLink>
    );
  }

  return (
    <div className="sidebar-item-wrapper" style={{ paddingLeft: 16 + depth * 12 }}>
      {hasChildren ? (
        <button
          className={`sidebar-item ${isActive ? 'active' : ''} has-children`}
          onClick={onToggle}
          aria-expanded={isOpen}
          aria-controls={`sidebar-${item.path}`}
          style={{ width: '100%', textAlign: 'left', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: '10px 12px', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 10 }}
        >
          <span className="sidebar-icon">{item.icon}</span>
          <span className="sidebar-label">{item.label}</span>
          {item.badge && <span className="sidebar-badge">{item.badge}</span>}
          <ChevronDownIcon className={`sidebar-chevron ${isOpen ? 'open' : ''}`} />
        </button>
      ) : (
        <NavLink
          to={item.path}
          className={`sidebar-item ${isActive ? 'active' : ''}`}
          style={{ paddingLeft: 16 + depth * 12 }}
        >
          <span className="sidebar-icon">{item.icon}</span>
          <span className="sidebar-label">{item.label}</span>
          {item.badge && <span className="sidebar-badge">{item.badge}</span>}
        </NavLink>
      )}
      <AnimatePresence mode="popLayout">
        {hasChildren && isOpen && (
          <div id={`sidebar-${item.path}`} className="sidebar-children" style={{ overflow: 'hidden' }}>
            {item.children!.map(child => (
              <SidebarItem key={child.path} item={child} isCollapsed={isCollapsed} isOpen={false} onToggle={() => {}} depth={depth + 1} />
            ))}
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

function SidebarSection({ title, items, isCollapsed }: { title: string; items: NavItem[]; isCollapsed: boolean }) {
  const [openSections, setOpenSections] = useState<Set<string>>(new Set());

  return (
    <div className="sidebar-section">
      {!isCollapsed && <h3 className="sidebar-section-title">{title}</h3>}
      {items.map(item => (
        <SidebarItem
          key={item.path}
          item={item}
          isCollapsed={isCollapsed}
          isOpen={openSections.has(item.path)}
          onToggle={() => setOpenSections(prev => {
            const next = new Set(prev);
            if (next.has(item.path)) next.delete(item.path);
            else next.add(item.path);
            return next;
          })}
        />
      ))}
    </div>
  );
}

export function Sidebar({ isCollapsed, onToggleCollapse }: { isCollapsed: boolean; onToggleCollapse: () => void }) {
  const { theme, toggleTheme, resolvedTheme } = useTheme();
  const { isOpen: paletteOpen, open: openPalette } = useCommandPalette({ items: [] });
  const reducedMotion = useReducedMotion();
  const location = useLocation();

  return (
    <aside
      className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        height: '100vh',
        width: isCollapsed ? 72 : 280,
        background: 'var(--color-bg-elevated)',
        borderRight: '1px solid var(--color-border)',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 100,
        transition: 'width 0.2s ease',
        overflow: 'hidden',
      }}
      aria-label="Main navigation"
    >
      <div className="sidebar-header" style={{ padding: '16px', borderBottom: '1px solid var(--color-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', minHeight: 64 }}>
        {!isCollapsed && (
          <NavLink to="/admin" className="sidebar-brand" style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--color-text-primary)', textDecoration: 'none', fontWeight: 700, fontSize: 18, letterSpacing: -0.5 }}>
            <LeadPilotIcon />
            <span>LeadPilot</span>
          </NavLink>
        )}
        <button
          onClick={onToggleCollapse}
          className="sidebar-toggle"
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          style={{ padding: 8, borderRadius: 8, background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)', cursor: 'pointer' }}
        >
          <ChevronLeftRightIcon />
        </button>
      </div>

      <nav className="sidebar-nav" style={{ flex: 1, overflowY: 'auto', padding: '16px 8px' }} aria-label="Navigation">
        {navSections.map(section => (
          <SidebarSection key={section.title} title={section.title} items={section.items} isCollapsed={isCollapsed} />
        ))}
      </nav>

      <div className="sidebar-footer" style={{ padding: '16px', borderTop: '1px solid var(--color-border)' }}>
        {!isCollapsed && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <button
              onClick={toggleTheme}
              className="sidebar-item"
              aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
              style={{ width: '100%', justifyContent: 'flex-start' }}
            >
              <span className="sidebar-icon">{resolvedTheme === 'dark' ? <SunIcon /> : <MoonIcon />}</span>
              <span className="sidebar-label">{resolvedTheme === 'dark' ? 'Light mode' : 'Dark mode'}</span>
            </button>
            <button
              onClick={openPalette}
              className="sidebar-item"
              style={{ width: '100%', justifyContent: 'flex-start' }}
            >
              <span className="sidebar-icon"><CommandIcon /></span>
              <span className="sidebar-label">Command Palette</span>
              <kbd style={{ fontSize: 10, padding: '2px 6px', borderRadius: 4, background: 'var(--color-border)', color: 'var(--color-text-muted)' }}>⌘K</kbd>
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}

function LeadPilotIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5" />
      <path d="M2 12l10 5 10-5" />
    </svg>
  );
}

function DashboardIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /></svg>;
}
function LeadsIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>;
}
function IntegrationsIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" /></svg>;
}
function AccountsIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>;
}
function AIControlIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="20 6 9 17 4 12" /></svg>;
}
function MessageEngineIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>;
}
function VoiceAgentIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><line x1="12" y1="19" x2="12" y2="22" /><line x1="8" y1="22" x2="16" y2="22" /></svg>;
}
function CampaignsIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" /></svg>;
}
function JobsIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="2" x2="12" y2="22" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg>;
}
function LogsIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /><polyline points="10 9 9 9 8 9" /></svg>;
}
function PaymentsIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg>;
}
function SettingsIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg>;
}
function SunIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" /><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" /></svg>;
}
function MoonIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></svg>;
}
function CommandIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 3a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3H6a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3 3 3 0 0 0 3 3h12a3 3 0 0 0 3-3 3 3 0 0 0-3-3z" /></svg>;
}
function ChevronDownIcon({ className = '' }) {
  return <svg className={className} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ transition: 'transform 0.2s ease' }}><polyline points="6 9 12 15 18 9" /></svg>;
}
function ChevronLeftRightIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6" /><polyline points="9 18 15 12 9 6" /></svg>;
}