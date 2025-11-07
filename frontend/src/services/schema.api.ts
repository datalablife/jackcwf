import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const schemaAPI = {
  // Get complete schema for a data source
  getSchema: async (dataSourceId: string) => {
    const response = await apiClient.get(`/datasources/${dataSourceId}/schema`);
    return response.data;
  },

  // Get list of tables
  getTables: async (dataSourceId: string) => {
    const response = await apiClient.get(
      `/datasources/${dataSourceId}/schema/tables`
    );
    return response.data;
  },

  // Get columns for a specific table
  getTableColumns: async (dataSourceId: string, tableName: string) => {
    const response = await apiClient.get(
      `/datasources/${dataSourceId}/schema/tables/${tableName}`
    );
    return response.data;
  },
};
