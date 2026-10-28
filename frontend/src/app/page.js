"use client";
import { useEffect, useState } from "react";

export default function Dashboard() {
  const [envios, setEnvios] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/api/envios")
      .then((res) => res.json())
      .then((data) => setEnvios(data))
      .catch((err) => console.error("Error cargando envíos:", err));
  }, []);

  return (
    <div className="p-10 min-h-screen bg-gray-100 text-black">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Panel Logístico Central</h1>
      
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <table className="min-w-full text-left border-collapse">
          <thead className="bg-blue-900 text-white">
            <tr>
              <th className="px-6 py-4">Código de Rastreo</th>
              <th className="px-6 py-4">Cliente</th>
              <th className="px-6 py-4">Destino</th>
              <th className="px-6 py-4">Peso</th>
              <th className="px-6 py-4">Estado</th>
            </tr>
          </thead>
          <tbody>
            {envios.map((envio) => (
              <tr key={envio.codigo_rastreo} className="border-b hover:bg-gray-50">
                <td className="px-6 py-4 font-mono text-gray-600">{envio.codigo_rastreo}</td>
                <td className="px-6 py-4 font-medium text-gray-800">{envio.cliente}</td>
                <td className="px-6 py-4 text-gray-600">{envio.direccion_destino}</td>
                <td className="px-6 py-4 text-gray-600">{envio.peso_kg} kg</td>
                <td className="px-6 py-4">
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-yellow-200 text-yellow-800">
                    {envio.estado.toUpperCase()}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {envios.length === 0 && (
          <div className="p-6 text-center text-gray-500">
            No hay envíos registrados. Ejecuta el POST en tu API.
          </div>
        )}
      </div>
    </div>
  );
}