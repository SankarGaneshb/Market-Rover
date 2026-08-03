import React from 'react';
import { Calendar, ChevronRight, Info } from 'lucide-react';

const RightsTimeline = ({ timeline }) => {
  const steps = [
    { label: 'Announcement', date: timeline.announcement_date, key: 'announcement' },
    { label: 'Board Meeting', date: timeline.board_meeting_date, key: 'board_meeting' },
    { label: 'Board Approval', date: timeline.board_approval_date, key: 'board_approval' },
    { label: 'DLOF Filing', date: timeline.dlof_filing_date, key: 'dlof_filing' },
    { label: 'Record Date', date: timeline.record_date, key: 'record_date' },
    { label: 'Dispatch Date', date: timeline.lof_dispatch_date, key: 'lof_dispatch' },
    { label: 'Issue Opens', date: timeline.open_date, key: 'open_date' },
    { label: 'Renunciation', date: timeline.renunciation_date, key: 'renunciation' },
    { label: 'Issue Closes', date: timeline.close_date, key: 'close_date' },
    { label: 'Allotment', date: timeline.allotment_date, key: 'allotment' },
    { label: 'Refund/Unblock', date: timeline.refund_unblock_date, key: 'refund_unblock' },
    { label: 'Trading Appr.', date: timeline.trading_approval_date, key: 'trading_approval' },
    { label: 'Listing', date: timeline.listing_date, key: 'listing' },
  ];

  return (
    <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.05)' }}>
      <h3 style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1.5rem', fontSize: '1.1rem', fontWeight: 700 }}>
        <Calendar size={18} color="#22d3ee" /> 13-Step Rights Lifecycle
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {steps.map((step, index) => (
          <div key={step.key} style={{
            display: 'flex', alignItems: 'center', gap: '12px',
            padding: '10px 15px', borderRadius: '12px',
            background: step.date ? 'rgba(34,211,238,0.08)' : 'rgba(255,255,255,0.02)',
            border: `1px solid ${step.date ? 'rgba(34,211,238,0.2)' : 'rgba(255,255,255,0.05)'}`,
            opacity: step.date ? 1 : 0.5
          }}>
            <div style={{
              width: '24px', height: '24px', borderRadius: '50%',
              background: step.date ? '#22d3ee' : '#334155',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '0.7rem', fontWeight: 800, color: step.date ? '#000' : '#94a3b8'
            }}>
              {index + 1}
            </div>
            <div style={{ flex: 1 }}>
              <p style={{ fontSize: '0.85rem', fontWeight: 700, color: step.date ? '#f8fafc' : '#94a3b8' }}>{step.label}</p>
              {step.date && <p style={{ fontSize: '0.75rem', color: '#22d3ee' }}>{new Date(step.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</p>}
            </div>
            {!step.date && <Info size={14} color="#475569" title="TBD" />}
          </div>
        ))}
      </div>
    </div>
  );
};

export default RightsTimeline;
