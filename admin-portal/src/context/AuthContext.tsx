import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, onAuthStateChanged, signOut } from 'firebase/auth';
import { auth } from '../firebase';
import api from '../api';

interface UserProfile {
  user_id: string;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

interface AuthContextType {
  currentUser: User | null;
  profile: UserProfile | null;
  loading: boolean;
  isAdmin: boolean;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchProfile = async (user: User) => {
    try {
      // Endpoint is idempotent and returns user details including role
      // Explicitly attach the Firebase ID token to avoid timing issues
      // where the axios interceptor might not yet have auth.currentUser.
      let config = {} as any;
      if (user && typeof (user as any).getIdToken === 'function') {
        const token = await (user as any).getIdToken();
        config = { headers: { Authorization: `Bearer ${token}` } };
      }
      const response = await api.post('/users/register', {}, config);
      setProfile(response.data);
    } catch (error) {
      console.error('Error fetching user profile from database:', error);
      setProfile(null);
    }
  };

  const logout = async () => {
    await signOut(auth);
    setProfile(null);
    setCurrentUser(null);
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setLoading(true);
      if (user) {
        setCurrentUser(user);
        await fetchProfile(user);
      } else {
        setCurrentUser(null);
        setProfile(null);
      }
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const refreshProfile = async () => {
    if (currentUser) {
      await fetchProfile(currentUser);
    }
  };

  const isAdmin = profile?.role === 'admin';

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        profile,
        loading,
        isAdmin,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
