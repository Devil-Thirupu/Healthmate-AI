/**
 * Doctor Connect API service — HealthMate AI
 * All calls go through the shared `api` axios instance (auth headers auto-attached).
 */
import api from './api';

// ─── DOCTORS ──────────────────────────────────────────────────────────────

export const doctorsApi = {
  /** Create a new doctor profile */
  create: (data) => api.post('/doctors/', data),

  /** List all doctors for the current patient */
  list: (includeInactive = false) =>
    api.get('/doctors/', { params: { include_inactive: includeInactive } }),

  /** Get a single doctor by ID */
  get: (doctorId) => api.get(`/doctors/${doctorId}`),

  /** Update a doctor profile */
  update: (doctorId, data) => api.put(`/doctors/${doctorId}`, data),

  /** Soft-delete (deactivate) a doctor profile */
  deactivate: (doctorId) => api.delete(`/doctors/${doctorId}`),
};

// ─── CONNECTIONS ───────────────────────────────────────────────────────────

export const connectionsApi = {
  /** Request a connection with a doctor */
  request: (data) => api.post('/doctors/connections/request', data),

  /** List all connections (optionally filter by status) */
  list: (statusFilter = null) =>
    api.get('/doctors/connections', { params: statusFilter ? { status_filter: statusFilter } : {} }),

  /** Cancel (pending→cancelled) or disconnect (accepted→disconnected) */
  update: (connectionId, data) => api.patch(`/doctors/connections/${connectionId}`, data),
};

// ─── APPOINTMENTS ──────────────────────────────────────────────────────────

export const appointmentsApi = {
  /** Request a new appointment */
  request: (data) => api.post('/doctors/appointments', data),

  /** List all appointments (optionally filter by status) */
  list: (statusFilter = null) =>
    api.get('/doctors/appointments', { params: statusFilter ? { status_filter: statusFilter } : {} }),

  /** Get a specific appointment */
  get: (appointmentId) => api.get(`/doctors/appointments/${appointmentId}`),

  /** Cancel an appointment */
  cancel: (appointmentId) =>
    api.patch(`/doctors/appointments/${appointmentId}`, { status: 'cancelled' }),
};

// ─── ACCESS GRANTS ─────────────────────────────────────────────────────────

export const accessGrantsApi = {
  /** Create a new granular access grant for a doctor */
  create: (data) => api.post('/doctors/access-grants', data),

  /** List all access grants (active by default) */
  list: (activeOnly = true) =>
    api.get('/doctors/access-grants', { params: { active_only: activeOnly } }),

  /** Revoke an access grant immediately */
  revoke: (grantId) => api.delete(`/doctors/access-grants/${grantId}`),
};

// ─── PUBLIC GRANT VIEWER (no auth) ────────────────────────────────────────

/** Called by doctors when opening the shared grant link */
export const viewDoctorGrant = (grantToken) =>
  api.get(`/doctors/access-grants/view/${grantToken}`);
