import { StrictMode, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, NavLink, Route, Routes, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ThemeProvider, useTheme } from './theme/ThemeProvider';
import { ThemeToggle } from './theme/ThemeToggle';
import { Hero } from './components/Hero';
import { Background } from './three/Background';
import { CampaignWorkspace } from './CampaignWorkspace';
import './styles.css';

type Social = { platform: string; profile_url: string; username?: string | null; status: string };
type Lead = { id: number; business: { id: number; name: string; category?: string | null; categories: string[]; location: { address?: string | null; locality?: string | null; city?: string | null; region?: string | null; country?: string | null; latitude?: string | null; longitude?: string | null }; contact: { phone?: string | null }; website?: string | null; google: { place_id?: string | null; maps_url?: string | null; rating?: string | null; review_count?: number | null; business_status?: string | null }; social_profiles: Social[] }; lifecycle: string; score: { score: number; grade: string; reasons: string[] } };
type Integration = { provider: string; status: string; account_name: string; capabilities: string[]; configured: boolean; enabled: boolean; last_error?: string };
type ConnectedAccount = { provider: string; id: number | null; status: string; account_name: string; capabilities: string[]; connected_at?: string | null };
type ContactProfile = { phone_number: string; voice_phone: string; voice_phone_status: string; whatsapp_phone: string; whatsapp_phone_status: string; instagram_handle: string; facebook_handle: string; linkedin_url: string; threads_url: string; tiktok_handle: string; gmail_email: string; email_sender_name: string };

async function api(path: string, init: RequestInit = {}) { const response = await fetch('/api/v1' + path, { ...init, headers: { 'Content-Type': 'application/json', ...(init.headers || {}) } }); const body = await response.json().catch(() => null); if (!response.ok) throw Error(body?.detail || body?.error || 'Request failed'); return body; }
function Notice({ message }: { message: string }) { return message ? <div className="notice" role="status">{message}</div> : null; }
function OAuthCallback() { const [params] = useSearchParams(); const [message, setMessage] = useState('Connecting account...'); useEffect(() => { const code = params.get('code'); const state = params.get('state'); if (!code || !state) { setMessage('OAuth callback is missing code or state.'); return; } void api('/admin/oauth/callback', { method: 'POST', body: JSON.stringify({ code, state }) }).then(result => setMessage(`${result.provider} connected successfully. You can return to Integrations.`)).catch(e => setMessage(e instanceof Error ? e.message : 'Account connection failed')); }, [params]); return <section><p className="eyebrow">ACCOUNT VERIFICATION</p><h1>{message}</h1><NavLink className="primary-link" to="/integrations">Back to integrations</NavLink></section>; }
function value(text?: string | number | null) { return text === null || text === undefined || text === '' ? 'Not available' : String(text); }
function ExternalLink({ href, label }: { href?: string | null; label: string }) { if (!href) return null; return <a className="external-link" href={href} target="_blank" rel="noopener noreferrer" aria-label={label}>{label}</a>; }
function SocialLinks({ lead }: { lead: Lead }) { const links = [{ key: 'MAPS', label: 'Maps', href: lead.business.google.maps_url }, { key: 'WEBSITE', label: 'Website', href: lead.business.website }, ...lead.business.social_profiles.map(item => ({ key: item.platform, label: item.platform, href: item.profile_url }))]; return <div className="links" aria-label="Business external links">{links.map(link => <ExternalLink key={link.key} href={link.href} label={link.label} />)}</div>; }
function LeadCard({ lead }: { lead: Lead }) { const location = [lead.business.location.city || lead.business.location.locality, lead.business.location.region, lead.business.location.country].filter(Boolean).join(', '); return <article className="lead-card"><div className="lead-card-head"><div><p className="eyebrow">{value(lead.business.category)}</p><h2>{lead.business.name}</h2></div><strong className="score">{lead.score.score}<small>{lead.score.grade}</small></strong></div><p className="address">{value(lead.business.location.address)}</p><p className="muted">{value(location)} · {value(lead.business.contact.phone)}</p><div className="facts"><span>Rating {value(lead.business.google.rating)}</span><span>Reviews {value(lead.business.google.review_count)}</span><span>{value(lead.business.google.business_status)}</span></div><SocialLinks lead={lead}/><div className="card-actions"><NavLink to={'/leads/' + lead.id}>View profile</NavLink><NavLink to={'/leads/' + lead.id + '?audit=1'}>Audit</NavLink></div></article>; }
function LeadFinder() { const [form, setForm] = useState({ niche: '', location: '', keywords: '', limit: 20 }); const [leads, setLeads] = useState<Lead[]>([]); const [message, setMessage] = useState(''); const load = () => void api('/leads').then(setLeads).catch(e => setMessage(e.message)); useEffect(load, []); const search = async () => { try { const result = await api('/leads/discover', { method: 'POST', body: JSON.stringify(form) }); setMessage(`${result.created} new leads saved`); load(); } catch (e) { setMessage(e instanceof Error ? e.message : 'Google Places request failed'); } }; return <section><p className="eyebrow">PRIMARY ACQUISITION WORKFLOW</p><h1>Lead Finder</h1><Notice message={message}/><div className="finder-form">{(['niche', 'location', 'keywords'] as const).map(key => <label key={key}>{key}<input value={form[key]} placeholder={key === 'niche' ? 'Restaurant' : key === 'location' ? 'New York' : 'Italian'} onChange={e => setForm({ ...form, [key]: e.target.value })}/></label>)}<label>limit<input type="number" min="1" max="60" value={form.limit} onChange={e => setForm({ ...form, limit: Number(e.target.value) })}/></label><button onClick={search}>Find leads</button></div><div className="lead-grid">{leads.length ? leads.map(lead => <LeadCard key={lead.id} lead={lead}/>) : <div className="empty">No leads yet. Configure Google Places in Integrations to begin.</div>}</div></section>; }
function Leads() { const [leads, setLeads] = useState<Lead[]>([]); const [query, setQuery] = useState(''); useEffect(() => { void api('/leads').then(setLeads); }, []); const filtered = leads.filter(x => x.business.name.toLowerCase().includes(query.toLowerCase()) || x.lifecycle.toLowerCase().includes(query.toLowerCase())); return <section><h1>Leads / CRM</h1><input aria-label="Search leads" placeholder="Search business or status" value={query} onChange={e => setQuery(e.target.value)}/><div className="lead-grid">{filtered.map(lead => <LeadCard key={lead.id} lead={lead}/>)}</div></section>; }
function LeadDetail() { const { id } = useParams(); const [lead, setLead] = useState<Lead | null>(null); const [message, setMessage] = useState(''); useEffect(() => { void api('/leads/' + id).then(setLead).catch(e => setMessage(e.message)); }, [id]); if (!lead) return <section><Notice message={message}/><p>Loading profile...</p></section>; const location = [lead.business.location.city || lead.business.location.locality, lead.business.location.region, lead.business.location.country].filter(Boolean).join(', '); return <section><NavLink to="/leads">Back to leads</NavLink><div className="profile-header"><div><p className="eyebrow">BUSINESS PROFILE</p><h1>{lead.business.name}</h1><p className="muted">{value(lead.business.category)} · {value(location)}</p></div><strong className="score large">{lead.score.score}<small>{lead.score.grade}</small></strong></div><SocialLinks lead={lead}/><div className="detail-grid">{[['Business', lead.business.name], ['Location', lead.business.location.address], ['City', location], ['Phone', lead.business.contact.phone], ['Rating', lead.business.google.rating], ['Reviews', lead.business.google.review_count], ['Google status', lead.business.google.business_status], ['Website audit', 'Not audited']].map(([label, detail]) => <article key={label}><span className="muted">{label}</span><strong>{value(detail)}</strong></article>)}</div><h2>Social Profiles</h2><div className="table">{lead.business.social_profiles.length ? lead.business.social_profiles.map(profile => <div className="item" key={profile.profile_url}><strong>{profile.platform}</strong><ExternalLink href={profile.profile_url} label={profile.profile_url}/></div>) : <div className="empty">No verified business social profiles are stored.</div>}</div></section>; }
function AIControl() {
  const [profile, setProfile] = useState<any>(null);
  const [preview, setPreview] = useState<{ subject: string; body: string } | null>(null);
  const [message, setMessage] = useState('');
  const [test, setTest] = useState({ business_name: 'Test business', website: '', website_status: 'unknown', previous_conversation: '', custom_instruction: '' });
  useEffect(() => { void api('/admin/instructions').then((items: any[]) => setProfile(items.find(item => item.active) || items[0] || { name: 'Default outreach', tone: 'Professional', language: 'English', services: '', offer: '', cta: '', rules: '', do_not_say: '', personalization_rules: '', additional_instructions: '' })).catch(error => setMessage(error.message)); }, []);
  const update = (key: string, value: string) => setProfile((current: any) => ({ ...current, [key]: value }));
  const save = async () => { try { const result = await api(profile.id ? `/admin/instructions/${profile.id}` : '/admin/instructions', { method: profile.id ? 'PUT' : 'POST', body: JSON.stringify(profile) }); setProfile(result); setMessage('AI instructions saved'); } catch (error) { setMessage(error instanceof Error ? error.message : 'AI settings save failed'); } };
  const runPreview = async () => { try { const result = await api('/admin/ai-control/preview', { method: 'POST', body: JSON.stringify({ ...test, instruction_profile_id: profile?.id }) }); setPreview(result); setMessage('TEST / SIMULATION only: no production record was created'); } catch (error) { setMessage(error instanceof Error ? error.message : 'AI preview failed'); } };
  if (!profile) return <section><p>Loading AI Control...</p></section>;
  return <section><p className="eyebrow">CONFIGURABLE AI</p><h1>AI Control</h1><Notice message={message}/><div className="admin-grid"><article className="panel"><h2>Messaging AI instructions</h2><label>Profile name<input value={profile.name || ''} onChange={event => update('name', event.target.value)}/></label><label>Service description<textarea value={profile.services || ''} onChange={event => update('services', event.target.value)}/></label><label>Offer<textarea value={profile.offer || ''} onChange={event => update('offer', event.target.value)}/></label><label>Custom rules<textarea value={profile.rules || ''} onChange={event => update('rules', event.target.value)}/></label><label>Do not say<textarea value={profile.do_not_say || ''} onChange={event => update('do_not_say', event.target.value)}/></label><label>Personalization rules<textarea value={profile.personalization_rules || ''} onChange={event => update('personalization_rules', event.target.value)}/></label><label>CTA<textarea value={profile.cta || ''} onChange={event => update('cta', event.target.value)}/></label><div className="row"><label>Tone<select value={profile.tone || 'Professional'} onChange={event => update('tone', event.target.value)}><option>Professional</option><option>Friendly</option><option>Casual</option><option>Direct</option><option>Consultative</option></select></label><label>Language<select value={profile.language || 'English'} onChange={event => update('language', event.target.value)}><option>English</option><option>Urdu</option><option>Urdu + English</option><option>Auto Detect</option></select></label></div><button onClick={() => void save()}>Save AI instructions</button></article><article className="panel"><h2>TEST / SIMULATION</h2><label>Business<input value={test.business_name} onChange={event => setTest({ ...test, business_name: event.target.value })}/></label><label>Website<input value={test.website} onChange={event => setTest({ ...test, website: event.target.value })}/></label><label>Website status<input value={test.website_status} onChange={event => setTest({ ...test, website_status: event.target.value })}/></label><label>Previous conversation<textarea value={test.previous_conversation} onChange={event => setTest({ ...test, previous_conversation: event.target.value })}/></label><button onClick={() => void runPreview()}>Generate preview</button>{preview && <article className="preview-list"><h3>{preview.subject}</h3><p>{preview.body}</p></article>}</article></div></section>;
}
function CommunicationHistory() { const [items, setItems] = useState<any[]>([]); const [message, setMessage] = useState(''); useEffect(() => { void api('/communication-history').then(setItems).catch(error => setMessage(error.message)); }, []); return <section><h1>Communication History</h1><Notice message={message}/><div className="table">{items.length ? items.map(item => <article className="item" key={`${item.type}-${item.id}`}><strong>{item.channel} · Lead {item.lead_id || 'unknown'}</strong><span>From: {item.sender || 'unknown'} · Status: {item.status}</span><span>Provider ID: {item.provider_message_id || 'not returned'}</span><span>{item.error || ''}</span></article>) : <div className="empty">No provider-backed communication history yet.</div>}</div></section>; }
const providerMeta: Record<string, { label: string; mark: string; color: string; oauth?: string }> = {
  'google-places': { label: 'Google Maps', mark: 'G', color: '#4285f4' },
  gmail: { label: 'Gmail', mark: 'M', color: '#ea4335', oauth: 'GMAIL' },
  whatsapp: { label: 'WhatsApp', mark: 'W', color: '#25d366' },
  instagram: { label: 'Instagram', mark: '◎', color: '#e1306c', oauth: 'META' },
  facebook: { label: 'Facebook', mark: 'f', color: '#1877f2', oauth: 'META' },
  linkedin: { label: 'LinkedIn', mark: 'in', color: '#0a66c2', oauth: 'LINKEDIN' },
  x: { label: 'X', mark: 'X', color: '#111111', oauth: 'X' },
  tiktok: { label: 'TikTok', mark: '♪', color: '#00f2ea', oauth: 'TIKTOK' },
  'voice-agent': { label: 'Voice calling', mark: '☎', color: '#ffb000' },
};
function Integrations() {
  const providers = ['google-places', 'gmail', 'whatsapp', 'instagram', 'facebook', 'tiktok', 'linkedin', 'x', 'voice-agent'];
  const [state, setState] = useState<Record<string, Integration>>({});
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([]);
  const [secret, setSecret] = useState<Record<string, string>>({});
  const [account, setAccount] = useState<Record<string, string>>({});
  const [contact, setContact] = useState<ContactProfile>({
    phone_number: '',
    voice_phone: '',
    voice_phone_status: 'NOT_CONFIGURED',
    whatsapp_phone: '',
    whatsapp_phone_status: 'NOT_CONFIGURED',
    instagram_handle: '',
    facebook_handle: '',
    linkedin_url: '',
    threads_url: '',
    tiktok_handle: '',
    gmail_email: '',
    email_sender_name: '',
  });
  const [message, setMessage] = useState('');
  const [verificationCode, setVerificationCode] = useState('');

  useEffect(() => {
    void Promise.allSettled(providers.map(provider => api('/admin/integrations/' + provider).then(value => setState(current => ({ ...current, [provider]: value })))))
      .then(results => { if (results.some(result => result.status === 'rejected')) setMessage('Some provider cards could not be loaded; configured cards remain available.'); });
    void api('/admin/contact-profile').then(setContact).catch(() => undefined);
    void api('/admin/accounts').then(setAccounts).catch(error => setMessage(error instanceof Error ? error.message : 'Accounts could not be loaded'));
  }, []);

  const save = async (provider: string) => {
    try {
      const value = await api('/admin/integrations/' + provider, { method: 'PUT', body: JSON.stringify({ account_name: account[provider] || '', secret_value: secret[provider] || '', enabled: true }) });
      setState(current => ({ ...current, [provider]: value }));
      setSecret({ ...secret, [provider]: '' });
      setMessage(provider + ' saved server-side');
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Save failed');
    }
  };

  const test = async (provider: string) => {
    try {
      const value = await api('/admin/integrations/' + provider + '/test', { method: 'POST' });
      setState(current => ({ ...current, [provider]: value }));
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Provider test failed');
    }
  };

  const connectOAuth = async (provider: string, targetProvider = provider) => {
    try {
      const redirectUri = window.location.origin + '/oauth/callback';
      setMessage(`Opening secure ${targetProvider} authorization...`);
      const result = await api('/admin/oauth/begin', { method: 'POST', body: JSON.stringify({ provider, target_provider: targetProvider, redirect_uri: redirectUri }) });
      window.location.assign(result.auth_url);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'OAuth connection could not start');
    }
  };

  const disconnectOAuth = async (provider: string) => {
    try {
      await api('/admin/accounts/' + provider, { method: 'DELETE' });
      setAccounts(current => current.map(item => item.provider === provider ? { ...item, status: 'DISCONNECTED', account_name: '', capabilities: [] } : item));
      setMessage(`${provider} disconnected`);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Disconnect failed');
    }
  };

  const requestPhoneVerification = async (key: 'voice_phone' | 'whatsapp_phone') => {
    try {
      const result = await api('/admin/contact-profile/' + key + '/verification-request', { method: 'POST' });
      setMessage(result.message);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Phone verification could not start');
    }
  };

  const confirmPhoneVerification = async () => {
    try {
      const result = await api('/admin/contact-profile/whatsapp_phone/verification-confirm', { method: 'POST', body: JSON.stringify({ code: verificationCode }) });
      setContact(current => ({ ...current, whatsapp_phone_status: result.status }));
      setVerificationCode('');
      setMessage('WhatsApp number verified');
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'WhatsApp verification failed');
    }
  };

  const saveContact = async () => {
    try {
      const value = await api('/admin/contact-profile', { method: 'PUT', body: JSON.stringify(contact) });
      setContact(value);
      setMessage('Contact profile saved');
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Contact save failed');
    }
  };

  return <section><h1>My Accounts</h1><p className="muted">Accounts are connected only after official provider authorization and backend verification.</p><Notice message={message}/><div className="admin-grid">
    {providers.map(provider => {
      const meta = providerMeta[provider];
      const accountProvider = ['whatsapp', 'instagram', 'facebook'].includes(provider) ? 'META' : provider.toUpperCase();
      const connected = accounts.find(item => item.provider === accountProvider);
      const item = state[provider];
      const isConnected = connected?.status === 'ACTIVE';
      const oauthProvider = meta?.oauth;
      return <article className="provider-card" key={provider}><div className="provider-heading"><span className="provider-mark" style={{ background: meta.color }}>{meta.mark}</span><div><h2>{meta.label}</h2><strong className="status">{connected?.status || item?.status || 'NOT_CONNECTED'}</strong></div></div><p>{connected?.account_name || item?.account_name || 'No verified account connected'}</p><div className="capability-list">{connected?.capabilities?.length ? connected.capabilities.map(capability => <span key={capability}>{capability}</span>) : <span>No verified capabilities</span>}</div>{oauthProvider && !isConnected && <button className="connect-button" onClick={() => void connectOAuth(oauthProvider, provider.toUpperCase())}>Connect with official {meta.label} authorization</button>}{oauthProvider && isConnected && <div className="stack-actions"><button onClick={() => void connectOAuth(oauthProvider, provider.toUpperCase())}>Reconnect</button><button onClick={() => void disconnectOAuth(accountProvider)}>Disconnect</button></div>}{!oauthProvider && <p className="muted">Configured through existing service settings.</p>}</article>;
    })}
  </div></section>;

  return <section><h1>Accounts & Integrations</h1><Notice message={message}/><div className="admin-grid">
    <article className="panel contact-panel"><h2>Your sending number</h2><p>Yehi ek number WhatsApp messaging aur voice calling dono ke liye use hoga.</p><div className="finder-form"><label>WhatsApp + voice phone<input placeholder="+923001234567" value={contact.phone_number} onChange={e => setContact({ ...contact, phone_number: e.target.value, voice_phone: e.target.value, whatsapp_phone: e.target.value })}/><span className={'verification-state ' + contact.whatsapp_phone_status}>{contact.whatsapp_phone_status}<button type="button" onClick={() => void requestPhoneVerification('whatsapp_phone')}>Request code</button></span></label><label>WhatsApp verification code<input inputMode="numeric" value={verificationCode} onChange={e => setVerificationCode(e.target.value)} placeholder="6-digit code"/><button type="button" disabled={!verificationCode} onClick={() => void confirmPhoneVerification()}>Confirm code</button></label>{(['instagram_handle', 'facebook_handle', 'linkedin_url', 'threads_url', 'tiktok_handle', 'gmail_email', 'email_sender_name'] as const).map(key => <label key={key}>{key.replace(/_/g, ' ')}<input value={contact[key]} onChange={e => setContact({ ...contact, [key]: e.target.value })}/></label>)}<button onClick={() => void saveContact()}>Save profile</button></div></article>
    {providers.map(provider => { const meta = providerMeta[provider]; const item = state[provider]; return <article className="provider-card" key={provider}><div className="provider-heading"><span className="provider-mark" style={{ background: meta.color }}>{meta.mark}</span><div><h2>{meta.label}</h2><strong className="status">{item?.status || 'NOT_CONFIGURED'}</strong></div></div><p>{item?.account_name || 'No account connected'}</p><input aria-label={provider + ' account'} placeholder="Account / sender identity" value={account[provider] || ''} onChange={e => setAccount({ ...account, [provider]: e.target.value })}/>{meta.oauth ? <button className="connect-button" onClick={() => void connectOAuth(meta.oauth!)}>Connect official account</button> : <input aria-label={provider + ' credential'} type="password" placeholder="Provider credential" value={secret[provider] || ''} onChange={e => setSecret({ ...secret, [provider]: e.target.value })}/>}<div className="stack-actions"><button onClick={() => void save(provider)}>Save</button><button onClick={() => void test(provider)}>Verify</button></div></article>; })}
  </div></section>;
}

function Campaigns() { const [name, setName] = useState(''); const [channel, setChannel] = useState('EMAIL'); const [sender, setSender] = useState(''); const [integrations, setIntegrations] = useState<Integration[]>([]); const [campaigns, setCampaigns] = useState<Array<{ id: number; name: string; channel: string; sender_account: string; status: string }>>([]); const [message, setMessage] = useState(''); const load = () => void api('/campaigns').then(setCampaigns); useEffect(() => { load(); void api('/admin/integrations').then(setIntegrations); }, []); const create = async () => { try { await api('/campaigns', { method: 'POST', body: JSON.stringify({ name, channel, sender_account: sender, lead_ids: [] }) }); setName(''); load(); } catch (e) { setMessage(e instanceof Error ? e.message : 'Campaign creation failed'); } }; const senders = integrations.filter(item => item.status === 'CONNECTED' && item.capabilities.some(capability => capability.toLowerCase().includes(channel.toLowerCase()))); return <section><h1>Campaigns</h1><Notice message={message}/><div className="row campaign-form"><input placeholder="Campaign name" value={name} onChange={e => setName(e.target.value)}/><select value={channel} onChange={e => { setChannel(e.target.value); setSender(''); }}><option>EMAIL</option><option>WHATSAPP</option><option>INSTAGRAM</option><option>FACEBOOK</option><option>LINKEDIN</option><option>X</option><option>TIKTOK</option></select><select aria-label="User sender account" value={sender} onChange={e => setSender(e.target.value)}><option value="">Select user sender account</option>{senders.map(item => <option key={item.provider} value={item.account_name}>{item.account_name}</option>)}</select><button disabled={!name || !sender} onClick={create}>Create</button></div>{!senders.length && <p className="muted">No connected sender account supports {channel}. Configure and test the owner's account first.</p>}{campaigns.map(campaign => <article className="item" key={campaign.id}><strong>{campaign.name}</strong><span>{campaign.channel} · {campaign.sender_account || 'No sender'} · {campaign.status}</span></article>)}</section>; }
function Dashboard() {
  const [metrics, setMetrics] = useState<Record<string, number>>({});
  useEffect(() => { void api('/dashboard/metrics').then(setMetrics); }, []);

  return (
    <section className="dashboard-shell">
      <Hero />
      <div className="stats-grid">
        {['leads', 'websites', 'qualified', 'contacted', 'customers', 'projects', 'campaigns', 'active_jobs'].map(key => (
          <article key={key} className="stat-card">
            <span>{key.replace('_', ' ')}</span>
            <strong>{metrics[key] ?? 0}</strong>
          </article>
        ))}
      </div>
    </section>
  );
}

function App() {
  const { theme } = useTheme();
  const [themeSettings, setThemeSettings] = useState({ theme: 'OBSIDIAN', reduced_motion: false, available_themes: ['OBSIDIAN', 'AURORA'] as string[] });
  const [themeMessage, setThemeMessage] = useState('');

  useEffect(() => {
    void api('/admin/theme').then(setThemeSettings).catch(() => setThemeSettings({ theme: 'OBSIDIAN', reduced_motion: false, available_themes: ['OBSIDIAN', 'AURORA'] }));
  }, []);

  const applyTheme = async (nextTheme: string) => {
    try {
      const next = { ...themeSettings, theme: nextTheme, reduced_motion: themeSettings.reduced_motion };
      const result = await api('/admin/theme', { method: 'PUT', body: JSON.stringify(next) });
      setThemeSettings(result);
      setThemeMessage(`Theme set to ${result.theme}`);
    } catch (error) {
      setThemeMessage(error instanceof Error ? error.message : 'Theme update failed');
    }
  };

  const currentTheme = themeSettings.theme === 'AURORA' ? 'AURORA' : 'OBSIDIAN';

  return (
    <>
      <ThemeToggle />
      <Background theme={currentTheme} reducedMotion={themeSettings.reduced_motion} />
      <div className="shell-frame">
        <aside>
          <div className="brand">LEAD<span>PILOT</span></div>
          <nav>
            {[['Dashboard', '/'], ['Lead Finder', '/lead-finder'], ['Leads', '/leads'], ['Campaigns', '/campaigns'], ['Campaign workspace', '/campaign-workspace'], ['Admin', '/admin'], ['Integrations', '/integrations']].map(([label, path]) => <NavLink key={path} to={path}>{label}</NavLink>)}
          </nav>
          <div className="theme-panel">
            <span className="eyebrow">Theme</span>
            <div className="theme-switcher">
              {themeSettings.available_themes.map(option => (
                <button key={option} className={currentTheme === option ? 'active' : ''} onClick={() => void applyTheme(option)}>{option}</button>
              ))}
            </div>
            {themeMessage && <small>{themeMessage}</small>}
          </div>
        </aside>
        <main>
          <Routes>
            <Route path="/" element={<Dashboard/>}/>
            <Route path="/lead-finder" element={<LeadFinder/>}/>
            <Route path="/leads" element={<Leads/>}/>
            <Route path="/leads/:id" element={<LeadDetail/>}/>
            <Route path="/oauth/callback" element={<OAuthCallback/>}/>
            <Route path="/campaigns" element={<Campaigns/>}/>
            <Route path="/campaign-workspace" element={<CampaignWorkspace/>}/>
            <Route path="/admin/ai-control" element={<AIControl/>}/>
            <Route path="/ai-control" element={<AIControl/>}/>
            <Route path="/communication-history" element={<CommunicationHistory/>}/>
            <Route path="/admin" element={<Integrations/>}/>
            <Route path="/integrations" element={<Integrations/>}/>
          </Routes>
        </main>
      </div>
    </>
  );
}
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <App />
      </ThemeProvider>
    </BrowserRouter>
  </StrictMode>
);
