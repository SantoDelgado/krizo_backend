from typing import Tuple, Optional
import os
import aiohttp
from fastapi import HTTPException, status
from database.models import Location
import math

class GeolocationService:
    def __init__(self):
        self.google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.distance_matrix_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        self.geocoding_url = "https://maps.googleapis.com/maps/api/geocode/json"

    async def calculate_distance(
        self,
        origin: Location,
        destination: Location
    ) -> Tuple[float, float]:
        """
        Calcula la distancia y tiempo estimado entre dos ubicaciones usando la API de Google Maps
        Retorna una tupla con (distancia_en_km, tiempo_en_minutos)
        """
        if not self.google_maps_api_key:
            # Si no hay API key, usar cálculo aproximado
            return self._calculate_approximate_distance(origin, destination)

        params = {
            "origins": f"{origin.latitude},{origin.longitude}",
            "destinations": f"{destination.latitude},{destination.longitude}",
            "key": self.google_maps_api_key,
            "mode": "driving"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.distance_matrix_url, params=params) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error al calcular la distancia"
                    )

                data = await response.json()
                if data["status"] != "OK":
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error en la respuesta de Google Maps"
                    )

                element = data["rows"][0]["elements"][0]
                if element["status"] != "OK":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No se pudo calcular la ruta"
                    )

                # Convertir metros a kilómetros y segundos a minutos
                distance_km = element["distance"]["value"] / 1000
                duration_minutes = element["duration"]["value"] / 60

                return distance_km, duration_minutes

    def _calculate_approximate_distance(
        self,
        origin: Location,
        destination: Location
    ) -> Tuple[float, float]:
        """
        Calcula una distancia aproximada usando la fórmula de Haversine
        Retorna una tupla con (distancia_en_km, tiempo_estimado_en_minutos)
        """
        # Radio de la Tierra en kilómetros
        R = 6371.0

        # Convertir coordenadas a radianes
        lat1, lon1 = math.radians(origin.latitude), math.radians(origin.longitude)
        lat2, lon2 = math.radians(destination.latitude), math.radians(destination.longitude)

        # Diferencia de coordenadas
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Fórmula de Haversine
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c

        # Estimar tiempo (asumiendo velocidad promedio de 30 km/h)
        estimated_time = (distance / 30) * 60  # en minutos

        return distance, estimated_time

    async def get_address_from_coordinates(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[str]:
        """
        Obtiene la dirección a partir de coordenadas usando la API de Google Maps
        """
        if not self.google_maps_api_key:
            return None

        params = {
            "latlng": f"{latitude},{longitude}",
            "key": self.google_maps_api_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.geocoding_url, params=params) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                if data["status"] != "OK" or not data["results"]:
                    return None

                return data["results"][0]["formatted_address"]

    async def get_coordinates_from_address(
        self,
        address: str
    ) -> Optional[Tuple[float, float]]:
        """
        Obtiene las coordenadas a partir de una dirección usando la API de Google Maps
        """
        if not self.google_maps_api_key:
            return None

        params = {
            "address": address,
            "key": self.google_maps_api_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.geocoding_url, params=params) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                if data["status"] != "OK" or not data["results"]:
                    return None

                location = data["results"][0]["geometry"]["location"]
                return location["lat"], location["lng"]

    def calculate_delivery_fee(
        self,
        distance_km: float,
        base_fee: float = 5.0,
        per_km_fee: float = 2.0
    ) -> float:
        """
        Calcula el costo de envío basado en la distancia
        """
        return base_fee + (distance_km * per_km_fee)

    def is_within_delivery_radius(
        self,
        origin: Location,
        destination: Location,
        max_radius_km: float = 10.0
    ) -> bool:
        """
        Verifica si la ubicación de destino está dentro del radio de entrega
        """
        distance, _ = self._calculate_approximate_distance(origin, destination)
        return distance <= max_radius_km 