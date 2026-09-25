import { useEffect, useState } from 'react';

type Lead = { id: number; business: { name: string; website?: string | null; contact: { phone?: string | null } } };

type Preview = { lead_id: number; business_name: string; website: string | null; subject: string; body: string };

async function api(path: string, init: RequestInit = {}) {
  const response = await fetch('/api/v1' + path, { ...init, headers: { 'Content-Type': 'application/json', ...(init.headers || {}) } });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw Error(body?.detail || 'Request failed');
  return body;
}

export function CampaignWorkspace() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [campaignId, setCampaignId] = useState('');
  const [channel, setChannel] = useState('EMAIL');
  const [sender, setSender] = useState('');
  const [name, setName] = useState('Restaurant outreach');
  const [preview, setPreview] = useState<Preview[]>([]);
  const [message, setMessage] = useState('');

  useEffect(() => { void api('/leads').then(setLeads).catch(error => setMessage(error.message)); }, []);
  const toggle = (id: number) => setSelected(current => current.includes(id) ? current.filter(item => item !== id) : [...current, id]);
  const create = async () => { if (!selected.length) return setMessage('Select at least one lead'); if (!sender.trim()) return setMessage('Select a connected sender account'); try { const result = await api('/campaigns', { method: 'POST', body: JSON.stringify({ name, channel, sender_account: sender.trim(), lead_ids: selected }) }); setCampaignId(String(result.id)); setMessage(`Campaign created for ${selected.length} leads`); } catch (error) { setMessage(error instanceof Error ? error.message : 'Campaign creation failed'); } };
  const prepare = async () => { if (!campaignId) return setMessage('Create a campaign first'); try { const result = await api(`/campaigns/${campaignId}/prepare`, { method: 'POST', body: JSON.stringify({ lead_ids: selected }) }); setPreview(result.previews); setMessage(`${result.count} message previews prepared`); } catch (error) { setMessage(error instanceof Error ? error.message : 'Preview failed'); } };
  const send = async () => { if (!campaignId) return setMessage('Create a campaign first'); try { const result = await api(`/campaigns/${campaignId}/send-selected`, { method: 'POST', body: JSON.stringify({ lead_ids: selected, channel }) }); setMessage(result.results.map((item: { lead_id: number; status: string }) => `Lead ${item.lead_id}: ${item.status}`).join(' | ')); } catch (error) { setMessage(error instanceof Error ? error.message : 'Send failed'); } };

  return <section><p className="eyebrow">CONTROLLED OUTREACH</p><h1>Campaign workspace</h1><div className="notice" role="status">{message || `${selected.length} leads selected`}</div><div className="campaign-toolbar"><input placeholder="Campaign name" value={name} onChange={event => setName(event.target.value)}/><select value={channel} onChange={event => setChannel(event.target.value)}><option>EMAIL</option><option>WHATSAPP</option><option>INSTAGRAM</option><option>FACEBOOK</option><option>LINKEDIN</option><option>X</option><option>TIKTOK</option></select><input placeholder="Connected sender account" value={sender} onChange={event => setSender(event.target.value)}/><button onClick={create}>Create campaign</button><button onClick={() => void prepare()}>Preview messages</button><button onClick={() => void send()}>Send selected once</button></div><div className="lead-select-list">{leads.map(lead => <label key={lead.id} className={selected.includes(lead.id) ? 'selected' : ''}><input type="checkbox" checked={selected.includes(lead.id)} onChange={() => toggle(lead.id)}/><span><strong>{lead.business.name}</strong><small>{lead.business.website ? `Website: ${lead.business.website}` : 'No website found'} · {lead.business.contact.phone || 'No phone'}</small></span></label>)}</div><div className="preview-list">{preview.map(item => <article key={item.lead_id}><strong>{item.business_name}</strong><small>{item.website ? 'Website-aware message' : 'No-website message'}</small><h3>{item.subject}</h3><p>{item.body}</p></article>)}</div></section>;
}
