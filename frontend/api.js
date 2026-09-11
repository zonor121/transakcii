import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

export const getParticipants = () => api.get('/participants').then(r => r.data);
export const getTransfers = (limit = 50) => api.get(`/transfers?limit=${limit}`).then(r => r.data);
export const doTransfer = (data) => api.post('/transfer', data).then(r => r.data);