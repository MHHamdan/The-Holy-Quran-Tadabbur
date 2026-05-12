import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, MapPin, Navigation, Clock, Phone, Globe, Loader2, Search, Filter, Compass, ExternalLink } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import clsx from 'clsx';

interface Place {
  id: string;
  name: string;
  name_ar?: string;
  type: 'mosque' | 'halal_restaurant' | 'islamic_center' | 'halal_market';
  lat: number;
  lon: number;
  distance?: number;
  address?: string;
  phone?: string;
  website?: string;
  opening_hours?: string;
  rating?: number;
  amenities?: string[];
}

interface Location {
  lat: number;
  lon: number;
}

const PLACE_TYPES = [
  { id: 'mosque', name_en: 'Mosques', name_ar: 'المساجد', icon: '🕌', osmTag: 'amenity=place_of_worship' },
  { id: 'halal_restaurant', name_en: 'Halal Restaurants', name_ar: 'المطاعم الحلال', icon: '🍽️', osmTag: 'cuisine=halal' },
  { id: 'islamic_center', name_en: 'Islamic Centers', name_ar: 'المراكز الإسلامية', icon: '🏛️', osmTag: 'amenity=community_centre' },
  { id: 'halal_market', name_en: 'Halal Markets', name_ar: 'أسواق الحلال', icon: '🛒', osmTag: 'shop=supermarket' },
];

const RADIUS_OPTIONS = [
  { value: 1000, label_en: '1 km', label_ar: '1 كم' },
  { value: 5000, label_en: '5 km', label_ar: '5 كم' },
  { value: 10000, label_en: '10 km', label_ar: '10 كم' },
  { value: 25000, label_en: '25 km', label_ar: '25 كم' },
];

export function MosqueFinderPage() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';

  const [location, setLocation] = useState<Location | null>(null);
  const [places, setPlaces] = useState<Place[]>([]);
  const [loading, setLoading] = useState(false);
  const [locationLoading, setLocationLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>('mosque');
  const [radius, setRadius] = useState(5000);
  const [selectedPlace, setSelectedPlace] = useState<Place | null>(null);
  const [qiblaDirection, setQiblaDirection] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Get user's location
  const getUserLocation = useCallback(() => {
    setLocationLoading(true);
    setError(null);

    if (!navigator.geolocation) {
      setError(isArabic ? 'تحديد الموقع غير مدعوم في متصفحك' : 'Geolocation is not supported by your browser');
      setLocationLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const loc = {
          lat: position.coords.latitude,
          lon: position.coords.longitude,
        };
        setLocation(loc);
        calculateQibla(loc.lat, loc.lon);
        setLocationLoading(false);
      },
      (err) => {
        let errorMsg = isArabic ? 'تعذر الحصول على موقعك' : 'Unable to get your location';
        if (err.code === 1) {
          errorMsg = isArabic ? 'يرجى السماح بالوصول إلى موقعك' : 'Please allow location access';
        }
        setError(errorMsg);
        setLocationLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }, [isArabic]);

  // Calculate Qibla direction
  function calculateQibla(lat: number, lon: number) {
    // Kaaba coordinates
    const kaabaLat = 21.4225;
    const kaabaLon = 39.8262;

    const latRad = (lat * Math.PI) / 180;
    const lonRad = (lon * Math.PI) / 180;
    const kaabaLatRad = (kaabaLat * Math.PI) / 180;
    const kaabaLonRad = (kaabaLon * Math.PI) / 180;

    const y = Math.sin(kaabaLonRad - lonRad);
    const x = Math.cos(latRad) * Math.tan(kaabaLatRad) - Math.sin(latRad) * Math.cos(kaabaLonRad - lonRad);
    let qibla = (Math.atan2(y, x) * 180) / Math.PI;

    // Normalize to 0-360
    qibla = (qibla + 360) % 360;
    setQiblaDirection(qibla);
  }

  // Fetch nearby places using Overpass API
  const fetchPlaces = useCallback(async () => {
    if (!location) return;

    setLoading(true);
    setError(null);

    try {
      // Build Overpass API query for mosques
      const overpassUrl = 'https://overpass-api.de/api/interpreter';

      let query = '';
      if (selectedType === 'mosque') {
        query = `
          [out:json][timeout:25];
          (
            node["amenity"="place_of_worship"]["religion"="muslim"](around:${radius},${location.lat},${location.lon});
            way["amenity"="place_of_worship"]["religion"="muslim"](around:${radius},${location.lat},${location.lon});
            node["building"="mosque"](around:${radius},${location.lat},${location.lon});
            way["building"="mosque"](around:${radius},${location.lat},${location.lon});
          );
          out body center;
        `;
      } else if (selectedType === 'halal_restaurant') {
        query = `
          [out:json][timeout:25];
          (
            node["cuisine"~"halal|muslim"](around:${radius},${location.lat},${location.lon});
            node["diet:halal"="yes"](around:${radius},${location.lat},${location.lon});
          );
          out body;
        `;
      } else if (selectedType === 'islamic_center') {
        query = `
          [out:json][timeout:25];
          (
            node["amenity"="community_centre"]["religion"="muslim"](around:${radius},${location.lat},${location.lon});
            node["name"~"islamic|muslim|masjid",i](around:${radius},${location.lat},${location.lon});
          );
          out body;
        `;
      } else {
        query = `
          [out:json][timeout:25];
          (
            node["shop"~"supermarket|convenience"]["diet:halal"="yes"](around:${radius},${location.lat},${location.lon});
            node["name"~"halal",i]["shop"](around:${radius},${location.lat},${location.lon});
          );
          out body;
        `;
      }

      const response = await fetch(overpassUrl, {
        method: 'POST',
        body: query,
      });

      if (!response.ok) {
        throw new Error('Failed to fetch places');
      }

      const data = await response.json();

      // Transform OSM data to our Place format
      const transformedPlaces: Place[] = data.elements.map((el: any) => {
        const lat = el.lat || el.center?.lat;
        const lon = el.lon || el.center?.lon;
        const distance = location ? calculateDistance(location.lat, location.lon, lat, lon) : undefined;

        return {
          id: el.id.toString(),
          name: el.tags?.name || el.tags?.['name:en'] || (isArabic ? 'مسجد' : 'Mosque'),
          name_ar: el.tags?.['name:ar'],
          type: selectedType as Place['type'],
          lat,
          lon,
          distance,
          address: el.tags?.['addr:full'] || el.tags?.['addr:street'],
          phone: el.tags?.phone,
          website: el.tags?.website,
          opening_hours: el.tags?.opening_hours,
        };
      });

      // Sort by distance
      transformedPlaces.sort((a, b) => (a.distance || 0) - (b.distance || 0));

      setPlaces(transformedPlaces);
    } catch (err) {
      console.error('Error fetching places:', err);
      setError(isArabic ? 'تعذر جلب الأماكن القريبة' : 'Failed to fetch nearby places');
    } finally {
      setLoading(false);
    }
  }, [location, selectedType, radius, isArabic]);

  // Calculate distance between two coordinates in meters
  function calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
    const R = 6371e3; // Earth's radius in meters
    const φ1 = (lat1 * Math.PI) / 180;
    const φ2 = (lat2 * Math.PI) / 180;
    const Δφ = ((lat2 - lat1) * Math.PI) / 180;
    const Δλ = ((lon2 - lon1) * Math.PI) / 180;

    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c;
  }

  function formatDistance(meters: number): string {
    if (meters < 1000) {
      return `${Math.round(meters)} ${isArabic ? 'متر' : 'm'}`;
    }
    return `${(meters / 1000).toFixed(1)} ${isArabic ? 'كم' : 'km'}`;
  }

  function openInMaps(place: Place) {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${place.lat},${place.lon}`;
    window.open(url, '_blank');
  }

  // Auto-fetch location on mount
  useEffect(() => {
    getUserLocation();
  }, []);

  // Fetch places when location or filters change
  useEffect(() => {
    if (location) {
      fetchPlaces();
    }
  }, [location, selectedType, radius, fetchPlaces]);

  // Filter places by search query
  const filteredPlaces = places.filter((place) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      place.name.toLowerCase().includes(query) ||
      place.name_ar?.toLowerCase().includes(query) ||
      place.address?.toLowerCase().includes(query)
    );
  });

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8" dir={isArabic ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/tools"
          className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 mb-4"
        >
          <ArrowLeft className={clsx('w-4 h-4', isArabic && 'rotate-180')} />
          {isArabic ? 'العودة للأدوات' : 'Back to Tools'}
        </Link>

        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 bg-teal-100 rounded-lg">
            <MapPin className="w-8 h-8 text-teal-600" />
          </div>
          <div>
            <h1 className={clsx('text-2xl font-bold text-gray-900', isArabic && 'font-arabic')}>
              {isArabic ? 'الخرائط الإسلامية' : 'Islamic Places Finder'}
            </h1>
            <p className="text-gray-600">
              {isArabic
                ? 'اعثر على المساجد والمطاعم الحلال والمراكز الإسلامية القريبة'
                : 'Find mosques, halal restaurants, and Islamic centers nearby'}
            </p>
          </div>
        </div>
      </div>

      {/* Qibla Direction */}
      {qiblaDirection !== null && (
        <div className="mb-6 p-4 bg-gradient-to-r from-teal-50 to-cyan-50 border border-teal-200 rounded-xl">
          <div className="flex items-center gap-4">
            <div className="relative w-16 h-16">
              <div className="absolute inset-0 rounded-full border-2 border-teal-300"></div>
              <div
                className="absolute inset-2 flex items-center justify-center"
                style={{ transform: `rotate(${qiblaDirection}deg)` }}
              >
                <Compass className="w-8 h-8 text-teal-600" />
              </div>
            </div>
            <div>
              <h3 className="font-semibold text-teal-800">
                {isArabic ? 'اتجاه القبلة' : 'Qibla Direction'}
              </h3>
              <p className="text-sm text-teal-600">
                {Math.round(qiblaDirection)}° {isArabic ? 'من الشمال' : 'from North'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Location Status */}
      {!location && (
        <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-xl text-center">
          {locationLoading ? (
            <div className="flex items-center justify-center gap-2 text-gray-600">
              <Loader2 className="w-5 h-5 animate-spin" />
              {isArabic ? 'جاري تحديد موقعك...' : 'Getting your location...'}
            </div>
          ) : (
            <div>
              <p className="text-gray-600 mb-3">
                {isArabic
                  ? 'نحتاج إلى موقعك لإظهار الأماكن القريبة'
                  : 'We need your location to show nearby places'}
              </p>
              <button
                onClick={getUserLocation}
                className="px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 inline-flex items-center gap-2"
              >
                <Navigation className="w-4 h-4" />
                {isArabic ? 'تحديد موقعي' : 'Get My Location'}
              </button>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="mb-6 space-y-4">
        {/* Place Type Tabs */}
        <div className="flex flex-wrap gap-2">
          {PLACE_TYPES.map((type) => (
            <button
              key={type.id}
              onClick={() => setSelectedType(type.id)}
              className={clsx(
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2',
                selectedType === type.id
                  ? 'bg-teal-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              )}
            >
              <span>{type.icon}</span>
              {isArabic ? type.name_ar : type.name_en}
            </button>
          ))}
        </div>

        {/* Search and Radius */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={isArabic ? 'ابحث عن مكان...' : 'Search places...'}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-500" />
            <select
              value={radius}
              onChange={(e) => setRadius(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            >
              {RADIUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {isArabic ? opt.label_ar : opt.label_en}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-teal-600" />
          </div>
        ) : filteredPlaces.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            {location
              ? (isArabic ? 'لم يتم العثور على أماكن قريبة' : 'No places found nearby')
              : (isArabic ? 'حدد موقعك للبحث' : 'Set your location to search')}
          </div>
        ) : (
          <>
            <p className="text-sm text-gray-600">
              {isArabic
                ? `تم العثور على ${filteredPlaces.length} مكان`
                : `Found ${filteredPlaces.length} places`}
            </p>
            {filteredPlaces.map((place) => (
              <PlaceCard
                key={place.id}
                place={place}
                language={language}
                onSelect={() => setSelectedPlace(place)}
                onNavigate={() => openInMaps(place)}
                formatDistance={formatDistance}
              />
            ))}
          </>
        )}
      </div>

      {/* Place Detail Modal */}
      {selectedPlace && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-lg w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-2">
              {isArabic && selectedPlace.name_ar ? selectedPlace.name_ar : selectedPlace.name}
            </h3>

            {selectedPlace.distance && (
              <p className="text-teal-600 text-sm mb-4 flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                {formatDistance(selectedPlace.distance)}
              </p>
            )}

            <div className="space-y-3 mb-6">
              {selectedPlace.address && (
                <div className="flex items-start gap-2 text-sm">
                  <MapPin className="w-4 h-4 text-gray-400 mt-0.5" />
                  <span className="text-gray-600">{selectedPlace.address}</span>
                </div>
              )}
              {selectedPlace.phone && (
                <div className="flex items-center gap-2 text-sm">
                  <Phone className="w-4 h-4 text-gray-400" />
                  <a href={`tel:${selectedPlace.phone}`} className="text-teal-600 hover:underline">
                    {selectedPlace.phone}
                  </a>
                </div>
              )}
              {selectedPlace.website && (
                <div className="flex items-center gap-2 text-sm">
                  <Globe className="w-4 h-4 text-gray-400" />
                  <a
                    href={selectedPlace.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-teal-600 hover:underline flex items-center gap-1"
                  >
                    {isArabic ? 'الموقع الإلكتروني' : 'Website'}
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              )}
              {selectedPlace.opening_hours && (
                <div className="flex items-start gap-2 text-sm">
                  <Clock className="w-4 h-4 text-gray-400 mt-0.5" />
                  <span className="text-gray-600">{selectedPlace.opening_hours}</span>
                </div>
              )}
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setSelectedPlace(null)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                {isArabic ? 'إغلاق' : 'Close'}
              </button>
              <button
                onClick={() => openInMaps(selectedPlace)}
                className="flex-1 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 flex items-center justify-center gap-2"
              >
                <Navigation className="w-4 h-4" />
                {isArabic ? 'الاتجاهات' : 'Directions'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Place Card Component
interface PlaceCardProps {
  place: Place;
  language: 'ar' | 'en';
  onSelect: () => void;
  onNavigate: () => void;
  formatDistance: (meters: number) => string;
}

function PlaceCard({ place, language, onSelect, onNavigate, formatDistance }: PlaceCardProps) {
  const isArabic = language === 'ar';
  const displayName = isArabic && place.name_ar ? place.name_ar : place.name;

  return (
    <div
      className="card border border-gray-200 hover:border-teal-300 transition-colors cursor-pointer"
      onClick={onSelect}
    >
      <div className="flex items-start gap-4">
        <div className="p-3 bg-teal-100 rounded-lg">
          <MapPin className="w-6 h-6 text-teal-600" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 mb-1">{displayName}</h3>
          {place.address && (
            <p className="text-sm text-gray-500 truncate">{place.address}</p>
          )}
          {place.distance && (
            <p className="text-sm text-teal-600 mt-1">
              {formatDistance(place.distance)}
            </p>
          )}
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onNavigate();
          }}
          className="p-2 text-teal-600 hover:bg-teal-50 rounded-lg"
          title={isArabic ? 'الاتجاهات' : 'Get Directions'}
        >
          <Navigation className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
