import { create } from 'zustand';

export interface DataSource {
  id: string;
  name: string;
  type: 'postgresql' | 'csv' | 'excel';
  status: 'connected' | 'disconnected' | 'error';
  created_date: string;
  connection_config?: {
    host?: string;
    port?: number;
    database?: string;
    username?: string;
  };
}

interface DataSourceStore {
  // State
  dataSources: DataSource[];
  selectedId: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchDataSources: () => Promise<void>;
  selectDataSource: (id: string) => void;
  addDataSource: (config: Omit<DataSource, 'id' | 'created_date'>) => Promise<void>;
  removeDataSource: (id: string) => Promise<void>;
  testConnection: (config: any) => Promise<boolean>;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
}

export const useDataSourceStore = create<DataSourceStore>((set, get) => ({
  // Initial state
  dataSources: [],
  selectedId: null,
  isLoading: false,
  error: null,

  // Actions
  fetchDataSources: async () => {
    set({ isLoading: true, error: null });
    try {
      // TODO: Implement API call
      // const response = await fetch('/api/datasources');
      // const data = await response.json();
      // set({ dataSources: data });
      set({ dataSources: [] });
    } catch (error) {
      set({ error: (error as Error).message });
    } finally {
      set({ isLoading: false });
    }
  },

  selectDataSource: (id: string) => {
    set({ selectedId: id });
  },

  addDataSource: async (config: Omit<DataSource, 'id' | 'created_date'>) => {
    set({ isLoading: true, error: null });
    try {
      // TODO: Implement API call to POST /api/datasources
      console.log('Adding datasource:', config);
    } catch (error) {
      set({ error: (error as Error).message });
    } finally {
      set({ isLoading: false });
    }
  },

  removeDataSource: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      // TODO: Implement API call to DELETE /api/datasources/{id}
      set((state) => ({
        dataSources: state.dataSources.filter((ds) => ds.id !== id),
      }));
    } catch (error) {
      set({ error: (error as Error).message });
    } finally {
      set({ isLoading: false });
    }
  },

  testConnection: async (config: any) => {
    set({ isLoading: true, error: null });
    try {
      // TODO: Implement API call to POST /api/datasources/{id}/test
      return true;
    } catch (error) {
      set({ error: (error as Error).message });
      return false;
    } finally {
      set({ isLoading: false });
    }
  },

  setError: (error: string | null) => {
    set({ error });
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading });
  },
}));
