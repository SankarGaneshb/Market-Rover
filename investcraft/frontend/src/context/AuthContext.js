import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('ic_token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      axios.get('/api/auth/me')
        .then(r => setUser(r.data.user))
        .catch(() => localStorage.removeItem('ic_token'))
        .finally(() => setLoading(false));
    } else setLoading(false);
  }, []);

  const login = async (googleToken) => {
    const { data } = await axios.post('/api/auth/google', { token: googleToken });
    localStorage.setItem('ic_token', data.token);
    axios.defaults.headers.common['Authorization'] = `Bearer ${data.token}`;
    setUser(data.user);
    return data; // includes is_new_user flag from backend
  };

  const logout = () => {
    localStorage.removeItem('ic_token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  return <AuthContext.Provider value={{ user, loading, login, logout }}>{!loading && children}</AuthContext.Provider>;
}
