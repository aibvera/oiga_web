const formato = new Intl.NumberFormat('es-PE', { style: 'currency', currency: 'PEN' })

// La API manda los precios como string ("24.90"). Se suma en céntimos para no arrastrar errores de float.
export const aCentimos = (precio) => Math.round(Number(precio) * 100)

export const soles = (centimos) => formato.format(centimos / 100)
