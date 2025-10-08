#!/bin/bash

# Script de monitoreo simple para Mariachi Fidelización
# Sin Docker, usando Python directo

echo "📊 Monitoreo de Mariachi Fidelización"
echo "======================================"

# Verificar estado del servicio
echo "🔧 Estado del servicio:"
sudo systemctl status mariachi-fidelizacion --no-pager

echo ""
echo "📈 Uso de recursos:"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memoria: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
echo "Disco: $(df -h / | awk 'NR==2{printf "%s", $5}')"

echo ""
echo "🌐 Estado de la aplicación:"
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Aplicación funcionando correctamente"
    echo "🌐 URL: http://$(curl -s ifconfig.me):8000"
else
    echo "❌ Aplicación no responde"
fi

echo ""
echo "📋 Logs recientes:"
sudo journalctl -u mariachi-fidelizacion --no-pager -n 10

echo ""
echo "🔧 Comandos útiles:"
echo "   Ver logs en tiempo real: sudo journalctl -u mariachi-fidelizacion -f"
echo "   Reiniciar servicio: sudo systemctl restart mariachi-fidelizacion"
echo "   Ver estado: sudo systemctl status mariachi-fidelizacion"
echo ""
