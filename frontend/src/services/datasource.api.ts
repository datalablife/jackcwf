import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface PostgresConnectionConfig {
  name: string;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
}

export const dataSourceAPI = {
  // List all data sources
  listDataSources: async () => {
    const response = await apiClient.get('/datasources');
    return response.data;
  },

  // Create PostgreSQL data source
  createPostgresDataSource: async (config: PostgresConnectionConfig) => {
    const response = await apiClient.post('/datasources/postgres', config);
    return response.data;
  },

  // Test connection
  testConnection: async (dataSourceId: string) => {
    const response = await apiClient.post(`/datasources/${dataSourceId}/test`);
    return response.data;
  },

  // Get data source details
  getDataSource: async (id: string) => {
    const response = await apiClient.get(`/datasources/${id}`);
    return response.data;
  },

  // Delete data source
  deleteDataSource: async (id: string) => {
    const response = await apiClient.delete(`/datasources/${id}`);
    return response.data;
  },
};
