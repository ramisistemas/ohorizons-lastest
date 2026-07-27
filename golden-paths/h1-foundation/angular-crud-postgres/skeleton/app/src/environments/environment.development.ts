export const environment = {
  production: false,
  // En desarrollo, proxy.conf.json reenvía /api -> http://localhost:3000 (PostgREST)
  apiUrl: '/api',
  resource: 'tasks',
};
