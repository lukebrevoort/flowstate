// Environment-specific configurations
interface Config {
  apiUrl: string;
  langGraphUrl: string;
}

// Development configuration
const devConfig: Config = {
  apiUrl: 'http://localhost:5001',
  langGraphUrl: 'http://localhost:9876',
};

// Production configuration
const prodConfig: Config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'https://api.flowstate.app',
  langGraphUrl: process.env.NEXT_PUBLIC_LANGGRAPH_URL || 'https://langgraph.flowstate.app',
};

// Determine which configuration to use based on environment
const config: Config = process.env.NODE_ENV === 'production' ? prodConfig : devConfig;

export default config;