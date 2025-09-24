// Script de inicialización para MongoDB
// Este script se ejecuta automáticamente cuando se inicia el contenedor MongoDB

print('🚀 Inicializando base de datos MongoDB para Arryn...');

// Crear usuario de aplicación
db = db.getSiblingDB('arryn_products_db');

db.createUser({
  user: 'arryn_app',
  pwd: 'arryn_app_password',
  roles: [
    {
      role: 'readWrite',
      db: 'arryn_products_db'
    }
  ]
});

print('✅ Usuario de aplicación creado: arryn_app');

// Crear colecciones e índices
db.createCollection('archivos');
db.createCollection('productos');
db.createCollection('ofertas');

// Índices para mejorar performance
db.archivos.createIndex({ "categoria": 1 });
db.archivos.createIndex({ "marca": 1 });
db.archivos.createIndex({ "precio_valor": 1 });
db.archivos.createIndex({ "fuente": 1 });
db.archivos.createIndex({ "fecha_extraccion": -1 });

// Índice compuesto para búsquedas complejas
db.archivos.createIndex({ 
  "categoria": 1, 
  "precio_valor": 1, 
  "fecha_extraccion": -1 
});

// Índice de texto para búsquedas
db.archivos.createIndex({ 
  "titulo": "text", 
  "marca": "text",
  "categoria": "text"
});

print('✅ Índices creados para colección archivos');

// Insertar datos de ejemplo (opcional)
db.archivos.insertMany([
  {
    "titulo": "iPhone 15 Pro",
    "marca": "APPLE",
    "precio_texto": "$999",
    "precio_valor": 999,
    "moneda": "USD",
    "categoria": "electronics",
    "imagen": "https://example.com/iphone15.jpg",
    "link": "https://example.com/iphone15",
    "fuente": "store_example",
    "fecha_extraccion": new Date(),
    "detalles_adicionales": "Smartphone de alta gama con cámara profesional"
  },
  {
    "titulo": "MacBook Air M3",
    "marca": "APPLE", 
    "precio_texto": "$1299",
    "precio_valor": 1299,
    "moneda": "USD",
    "categoria": "electronics",
    "imagen": "https://example.com/macbook.jpg",
    "link": "https://example.com/macbook",
    "fuente": "store_example",
    "fecha_extraccion": new Date(),
    "detalles_adicionales": "Laptop ultradelgada con chip M3"
  },
  {
    "titulo": "Nike Air Max 270",
    "marca": "NIKE",
    "precio_texto": "$150",
    "precio_valor": 150,
    "moneda": "USD", 
    "categoria": "shoes",
    "imagen": "https://example.com/airmax.jpg",
    "link": "https://example.com/airmax",
    "fuente": "store_example",
    "fecha_extraccion": new Date(),
    "detalles_adicionales": "Zapatillas deportivas con amortiguación Air"
  }
]);

print('✅ Datos de ejemplo insertados');
print('🎉 Inicialización de MongoDB completada exitosamente');

// Mostrar estadísticas
print('📊 Estadísticas de la base de datos:');
print('- Colecciones:', db.getCollectionNames());
print('- Documentos en archivos:', db.archivos.countDocuments());
print('- Índices en archivos:', db.archivos.getIndexes().length);