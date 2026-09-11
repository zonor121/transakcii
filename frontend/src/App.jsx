import { useState, useEffect } from 'react';
import { getParticipants, getTransfers, doTransfer } from './api';

function App() {
  const [participants, setParticipants] = useState([]);
  const [history, setHistory] = useState([]);
  const [form, setForm] = useState({ from_id: '', to_id: '', amount: '', transfer_type: 'SALARY', description: '' });
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const loadData = async () => {
    const [p, h] = await Promise.all([getParticipants(), getTransfers()]);
    setParticipants(p);
    setHistory(h);
  };

  useEffect(() => { loadData(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await doTransfer({ ...form, amount: parseFloat(form.amount) });
      setToast({ type: 'success', msg: res.message });
      setForm(prev => ({ ...prev, amount: '', description: '' }));
      await loadData();
    } catch (err) {
      setToast({ type: 'error', msg: err.response?.data?.detail || 'Ошибка сети' });
    } finally {
      setLoading(false);
      setTimeout(() => setToast(null), 3000);
    }
  };

  const totalMoney = participants.reduce((s, p) => s + parseFloat(p.balance), 0);

  return (
    <div style={{ maxWidth: 900, margin: '2rem auto', fontFamily: 'system-ui' }}>
      <h1>🌼 Магазин цветов "Ромашка"</h1>

      {/* Балансы */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        {participants.map(p => (
          <div key={p.id} style={{ background: '#fff', padding: '1.5rem', borderRadius: 12, border: '1px solid #e2e8f0', textAlign: 'center' }}>
            <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>{p.role}</div>
            <div style={{ fontWeight: 600, margin: '0.5rem 0' }}>{p.name}</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#10b981' }}>
              {parseFloat(p.balance).toLocaleString('ru-RU', { minimumFractionDigits: 2 })} ₽
            </div>
          </div>
        ))}
        <div style={{ background: '#ecfdf5', padding: '1.5rem', borderRadius: 12, border: '1px solid #a7f3d0', textAlign: 'center' }}>
          <div style={{ fontSize: '0.75rem', color: '#065f46', fontWeight: 600 }}>СИСТЕМА</div>
          <div style={{ fontWeight: 600, margin: '0.5rem 0' }}>Общая масса денег</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#059669' }}>
            {totalMoney.toLocaleString('ru-RU', { minimumFractionDigits: 2 })} ₽
          </div>
        </div>
      </div>

      {/* Форма перевода */}
      <form onSubmit={handleSubmit} style={{ background: '#fff', padding: '2rem', borderRadius: 12, border: '1px solid #e2e8f0', marginBottom: '2rem' }}>
        <h3 style={{ marginTop: 0 }}>💸 Новый перевод</h3>
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
          <select value={form.from_id} onChange={e => setForm({ ...form, from_id: e.target.value })} required
            style={{ flex: 1, padding: '0.75rem', borderRadius: 8, border: '1px solid #e2e8f0' }}>
            <option value="">Отправитель</option>
            {participants.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <select value={form.to_id} onChange={e => setForm({ ...form, to_id: e.target.value })} required
            style={{ flex: 1, padding: '0.75rem', borderRadius: 8, border: '1px solid #e2e8f0' }}>
            <option value="">Получатель</option>
            {participants.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </div>
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
          <input type="number" step="0.01" min="0.01" placeholder="Сумма (₽)" value={form.amount}
            onChange={e => setForm({ ...form, amount: e.target.value })} required
            style={{ flex: 1, padding: '0.75rem', borderRadius: 8, border: '1px solid #e2e8f0' }} />
          <select value={form.transfer_type} onChange={e => setForm({ ...form, transfer_type: e.target.value })}
            style={{ flex: 1, padding: '0.75rem', borderRadius: 8, border: '1px solid #e2e8f0' }}>
            <option value="SALARY">Зарплата</option>
            <option value="PAYMENT">Оплата</option>
          </select>
        </div>
        <input type="text" placeholder="Описание" value={form.description}
          onChange={e => setForm({ ...form, description: e.target.value })}
          style={{ width: '100%', padding: '0.75rem', borderRadius: 8, border: '1px solid #e2e8f0', marginBottom: '1rem', boxSizing: 'border-box' }} />
        <button type="submit" disabled={loading}
          style={{ width: '100%', padding: '0.75rem', background: '#10b981', color: '#fff', border: 'none', borderRadius: 8, fontSize: '1rem', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.6 : 1 }}>
          {loading ? 'Обработка...' : 'Выполнить перевод'}
        </button>
      </form>

      {/* История */}
      <h3> История транзакций</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse', background: '#fff', borderRadius: 12, overflow: 'hidden', border: '1px solid #e2e8f0' }}>
        <thead>
          <tr style={{ background: '#f1f5f9' }}>
            {['Дата', 'Тип', 'От → Кому', 'Сумма', 'Статус'].map(h =>
              <th key={h} style={{ padding: '1rem', textAlign: 'left', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>
            )}
          </tr>
        </thead>
        <tbody>
          {history.map(t => (
            <tr key={t.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
              <td style={{ padding: '1rem' }}>{new Date(t.created_at).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}</td>
              <td style={{ padding: '1rem' }}>{t.type}</td>
              <td style={{ padding: '1rem' }}>{t.from?.name} → {t.to?.name}</td>
              <td style={{ padding: '1rem' }}>{parseFloat(t.amount).toLocaleString('ru-RU', { minimumFractionDigits: 2 })} ₽</td>
              <td style={{ padding: '1rem', color: t.status === 'SUCCESS' ? '#10b981' : '#ef4444', fontWeight: 600 }}>{t.status}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Toast */}
      {toast && (
        <div style={{ position: 'fixed', bottom: '2rem', right: '2rem', padding: '1rem 1.5rem', borderRadius: 8, color: '#fff', fontWeight: 500, background: toast.type === 'success' ? '#10b981' : '#ef4444', zIndex: 100 }}>
          {toast.msg}
        </div>
      )}
    </div>
  );
}

export default App;