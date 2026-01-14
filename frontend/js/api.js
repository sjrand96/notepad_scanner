/**
 * API client for communicating with the backend.
 */

const API_BASE = '';

class API {
    static async getUsers() {
        const response = await fetch(`${API_BASE}/api/users`);
        if (!response.ok) {
            throw new Error('Failed to fetch users');
        }
        return response.json();
    }

    static async startSession(userId) {
        const response = await fetch(`${API_BASE}/api/session`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_id: userId }),
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to start session');
        }
        return response.json();
    }

    static async getPreview(sessionId) {
        const response = await fetch(`${API_BASE}/api/preview?session_id=${sessionId}`);
        if (!response.ok) {
            throw new Error('Failed to get preview');
        }
        return response.json();
    }

    static async capture(sessionId) {
        const response = await fetch(`${API_BASE}/api/capture`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ session_id: sessionId }),
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to capture');
        }
        return response.json();
    }

    static async review(sessionId) {
        const response = await fetch(`${API_BASE}/api/review`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ session_id: sessionId }),
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to review');
        }
        return response.json();
    }

    static async process(sessionId) {
        const response = await fetch(`${API_BASE}/api/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ session_id: sessionId }),
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to process');
        }
        return response.json();
    }

    static async endSession(sessionId) {
        const response = await fetch(`${API_BASE}/api/session/${sessionId}`, {
            method: 'DELETE',
        });
        if (!response.ok) {
            throw new Error('Failed to end session');
        }
        return response.json();
    }
}
