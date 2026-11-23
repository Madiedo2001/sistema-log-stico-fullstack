"use client";
import { useEffect, useState } from "react";

export default function Dashboard() {
  const [envios, setEnvios] = useState([]);

  useEffect(() => {
    // 1. Carga inicial de datos mediante la API REST
    fetch("http://127.0.0.1:8000/api/envios")
      .then((res) => res.json())
      .then((data) => setEnvios(data))
      .catch((err) => console.error("Error cargando envíos:", err));

    // 2. Conexión WebSocket para eventos en tiempo real
    const ws = new WebSocket("ws://127.0.0.1:8000/ws/envios");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.evento === "NUEVO_ENVIO") {
        setEnvios((prev) => [
          {
            codigo_rastreo: data.codigo_rastreo,
            estado: data.estado,
            cliente: data.cliente,
            descripcion: "Lote de Teclados Mecánicos",
            peso_kg: "15.50",
            direccion_destino: "Sucursal Norte",
          },
          ...prev,
        ]);
      } else if (data.evento === "ESTADO_ACTUALIZADO") {
        setEnvios((prev) =>
          prev.map((item) =>
            item.codigo_rastreo === data.codigo_rastreo
              ? { ...item, estado: data.estado }
              : item
          )
        );
      }
    };

    return () => ws.close();
  }, []);

  // Función auxiliar para asignar color según el estado del paquete
  const getBadgeStyle = (estado) => {
    switch (estado?.toLowerCase()) {
      case "entregado":
        return "bg-green-100 text-green-800 border border-green-300";
      case "en_transito":
        return "bg-blue-100 text-blue-800 border border-blue-300";
      default:
        return "bg-amber-100 text-amber-800 border border-amber-300";
    }
  };

  return (
    <div className="p-10 min-h-screen bg-gray-100 text-black">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">
        Panel Logístico Central
      </h1>

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
          <tbody className="divide-y divide-gray-200">
            {envios.map((item, idx) => (
              <tr key={idx} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 font-mono font-medium text-gray-700">
                  {item.codigo_rastreo}
                </td>
                <td className="px-6 py-4 text-gray-700">{item.cliente}</td>
                <td className="px-6 py-4 text-gray-600">
                  {item.direccion_destino}
                </td>
                <td className="px-6 py-4 text-gray-600">{item.peso_kg} kg</td>
                <td className="px-6 py-4">
                  <span
                    className={`px-3 py-1 text-xs font-semibold rounded-full uppercase tracking-wider ${getBadgeStyle(
                      item.estado
                    )}`}
                  >
                    {item.estado?.replace("_", " ")}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {envios.length === 0 && (
          <div className="p-6 text-center text-gray-500">
            No hay envíos registrados. Ejecuta la generación de datos en la API.
          </div>
        )}
      </div>
    </div>
  );
}