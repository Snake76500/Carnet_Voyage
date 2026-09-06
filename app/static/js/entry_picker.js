/**
 * Interactive GPS Picker for Day Entry creation & editing
 */

document.addEventListener('DOMContentLoaded', () => {
  const pickerMapEl = document.getElementById('picker-map');
  if (!pickerMapEl) return;

  const latInput = document.getElementById('latitude');
  const lngInput = document.getElementById('longitude');
  const locationInput = document.getElementById('location_name');

  // Initial Coordinates
  const initialLat = parseFloat(latInput.value) || 48.8566; // Default to Paris if empty
  const initialLng = parseFloat(lngInput.value) || 2.3522;
  const hasExistingCoords = !isNaN(parseFloat(latInput.value)) && !isNaN(parseFloat(lngInput.value));

  const map = L.map('picker-map').setView([initialLat, initialLng], hasExistingCoords ? 10 : 3);

  // Use official OpenStreetMap tiles (no API key required, 100% free)
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributeurs',
    maxZoom: 19
  }).addTo(map);

  // Custom marker
  let marker = null;

  function updateMarker(lat, lng, doReverseGeocode = false) {
    latInput.value = lat.toFixed(6);
    lngInput.value = lng.toFixed(6);

    if (!marker) {
      marker = L.marker([lat, lng], { draggable: true }).addTo(map);
      marker.on('dragend', (e) => {
        const pos = e.target.getLatLng();
        updateMarker(pos.lat, pos.lng, true);
      });
    } else {
      marker.setLatLng([lat, lng]);
    }

    // Optional reverse geocode to fetch city/region name
    if (doReverseGeocode && locationInput && !locationInput.value.trim()) {
      fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`)
        .then(res => res.json())
        .then(data => {
          if (data && data.display_name) {
            const parts = data.display_name.split(',');
            const shortName = parts.slice(0, 2).join(',').trim();
            locationInput.value = shortName || data.display_name;
          }
        })
        .catch(() => {});
    }
  }

  if (hasExistingCoords) {
    updateMarker(initialLat, initialLng, false);
  }

  // Click on map to place/move marker
  map.on('click', (e) => {
    updateMarker(e.latlng.lat, e.latlng.lng, true);
  });

  // --- Address Geocoding Search (OpenStreetMap Nominatim) ---
  const searchInput = document.getElementById('address-search-input');
  const searchBtn = document.getElementById('address-search-btn');
  const suggestionsList = document.getElementById('address-suggestions');

  if (searchInput && searchBtn && suggestionsList) {
    let debounceTimer = null;

    function performSearch(selectFirst = false) {
      const query = searchInput.value.trim();
      if (!query) {
        suggestionsList.style.display = 'none';
        return;
      }

      searchBtn.disabled = true;
      searchBtn.textContent = '...';

      fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`)
        .then(res => res.json())
        .then(results => {
          searchBtn.disabled = false;
          searchBtn.textContent = 'Rechercher';

          if (!results || results.length === 0) {
            suggestionsList.innerHTML = '<li class="address-suggestion-item" style="color: var(--text-muted); cursor: default;">Aucun lieu trouvé pour cette recherche.</li>';
            suggestionsList.style.display = 'block';
            return;
          }

          if (selectFirst) {
            selectLocation(results[0]);
            return;
          }

          suggestionsList.innerHTML = '';
          results.forEach(place => {
            const li = document.createElement('li');
            li.className = 'address-suggestion-item';
            li.innerHTML = `📍 <span>${place.display_name}</span>`;
            li.addEventListener('click', () => {
              selectLocation(place);
            });
            suggestionsList.appendChild(li);
          });
          suggestionsList.style.display = 'block';
        })
        .catch(err => {
          console.error('Erreur recherche d\'adresse :', err);
          searchBtn.disabled = false;
          searchBtn.textContent = 'Rechercher';
        });
    }

    function selectLocation(place) {
      const lat = parseFloat(place.lat);
      const lng = parseFloat(place.lon);
      updateMarker(lat, lng, false);
      map.setView([lat, lng], 14);

      // Pre-fill location name if empty or user wants it
      if (locationInput) {
        const parts = place.display_name.split(',');
        const shortName = parts.slice(0, 2).join(',').trim();
        locationInput.value = shortName || place.display_name;
      }

      suggestionsList.style.display = 'none';
      searchInput.value = place.display_name;
    }

    searchBtn.addEventListener('click', (e) => {
      e.preventDefault();
      performSearch(false);
    });

    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        performSearch(true);
      } else if (e.key === 'Escape') {
        suggestionsList.style.display = 'none';
      }
    });

    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      if (searchInput.value.trim().length >= 3) {
        debounceTimer = setTimeout(() => {
          performSearch(false);
        }, 400);
      } else {
        suggestionsList.style.display = 'none';
      }
    });

    // Close suggestions on outside click
    document.addEventListener('click', (e) => {
      if (!searchInput.contains(e.target) && !suggestionsList.contains(e.target) && !searchBtn.contains(e.target)) {
        suggestionsList.style.display = 'none';
      }
    });
  }

  // Dynamic Media Rows Management
  const mediaContainer = document.getElementById('media-container');
  const addMediaBtn = document.getElementById('add-media-btn');

  if (addMediaBtn && mediaContainer) {
    addMediaBtn.addEventListener('click', () => {
      const rowIndex = mediaContainer.children.length;
      const row = document.createElement('div');
      row.className = 'media-input-row';
      row.innerHTML = `
        <div class="media-input-header">
          <strong>Média #${rowIndex + 1}</strong>
          <button type="button" class="btn btn-danger btn-sm remove-media-btn">Supprimer</button>
        </div>
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">Type</label>
            <select name="media_type[]" class="form-control">
              <option value="photo">Photo (Lien direct ou Google Drive)</option>
              <option value="video">Vidéo (Lien YouTube)</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Légende (optionnelle)</label>
            <input type="text" name="media_caption[]" class="form-control" placeholder="Ex: Coucher de soleil sur le glacier" />
          </div>
        </div>
        <div class="form-group" style="margin-bottom: 0;">
          <label class="form-label">URL du média</label>
          <input type="url" name="media_url[]" class="form-control" placeholder="https://drive.google.com/... ou https://youtube.com/watch?v=..." required />
        </div>
      `;
      mediaContainer.appendChild(row);

      row.querySelector('.remove-media-btn').addEventListener('click', () => {
        row.remove();
      });
    });

    // Attach listener to existing delete buttons
    document.querySelectorAll('.remove-media-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.target.closest('.media-input-row').remove();
      });
    });
  }
});
