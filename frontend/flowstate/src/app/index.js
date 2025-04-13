import { useEffect, useState } from 'react';

export default function Home() {
  const [backendData, setBackendData] = useState(null);

  useEffect(() => {
    async function fetchData() {
      const response = await fetch('/api/backend');
      const data = await response.json();
      setBackendData(data);
    }

    fetchData();
  }, []);

  return (
    <div>
      {backendData ? (
        <h1>{backendData.message}</h1>
      ) : (
        <h1>Loading...</h1>
      )}
    </div>
  );
}
