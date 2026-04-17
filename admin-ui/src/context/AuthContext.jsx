import React, { createContext, useContext, useState } from "react";
import api from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem("admin_token") || null);
  const [username, setUsername] = useState(localStorage.getItem("admin_user") || null);

  const login = async (username, password) => {
    const res = await api.post("/auth/login", { username, password });
    const { token: tok, username: user } = res.data;
    localStorage.setItem("admin_token", tok);
    localStorage.setItem("admin_user", user);
    setToken(tok);
    setUsername(user);
    return true;
  };

  const logout = () => {
    localStorage.removeItem("admin_token");
    localStorage.removeItem("admin_user");
    setToken(null);
    setUsername(null);
  };

  return (
    <AuthContext.Provider value={{ token, username, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
