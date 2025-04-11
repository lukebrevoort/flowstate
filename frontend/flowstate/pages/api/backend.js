export default async function handler(req, res) {
    try {
      const response = await fetch('http://localhost:5000/api/test'); // Replace with your backend URL
      const data = await response.json();
      res.status(200).json(data);
    } catch (error) {
      console.error("Error fetching from backend:", error);
      res.status(500).json({ error: 'Failed to fetch data from backend' });
    }
  }
  