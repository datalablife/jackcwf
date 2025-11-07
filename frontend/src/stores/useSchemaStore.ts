import { create } from 'zustand';

export interface Schema {
  table_name: string;
  columns: {
    name: string;
    data_type: string;
  }[];
}

interface SchemaStore {
  // State
  schemas: Record<string, Schema[]>;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchSchema: (dataSourceId: string) => Promise<Schema[]>;
  clearSchema: (dataSourceId: string) => void;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
}

export const useSchemaStore = create<SchemaStore>((set, get) => ({
  // Initial state
  schemas: {},
  isLoading: false,
  error: null,

  // Actions
  fetchSchema: async (dataSourceId: string) => {
    set({ isLoading: true, error: null });
    try {
      // Check cache first
      const cached = get().schemas[dataSourceId];
      if (cached) {
        return cached;
      }

      // TODO: Implement API call to GET /api/datasources/{id}/schema
      const schema: Schema[] = [];
      set((state) => ({
        schemas: {
          ...state.schemas,
          [dataSourceId]: schema,
        },
      }));
      return schema;
    } catch (error) {
      set({ error: (error as Error).message });
      return [];
    } finally {
      set({ isLoading: false });
    }
  },

  clearSchema: (dataSourceId: string) => {
    set((state) => {
      const newSchemas = { ...state.schemas };
      delete newSchemas[dataSourceId];
      return { schemas: newSchemas };
    });
  },

  setError: (error: string | null) => {
    set({ error });
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading });
  },
}));
